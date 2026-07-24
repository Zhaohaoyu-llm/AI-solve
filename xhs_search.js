const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = path.join(__dirname, 'references', 'screenshots');
const DATA_DIR = path.join(__dirname, 'references');

const SEARCH_KEYWORDS = [
  '希腊酸奶 早餐',
  '轻食健身餐 上班族',
  '高蛋白早餐 快手',
  '减脂餐 博主',
];

const KNOWN_BLOGGERS = ['文静不pang', '绿柚柚 轻食', 'MissMe早餐'];

(async () => {
  console.log('=== 小红书博主自动化搜索 ===\n');

  const browser = await chromium.launch({
    headless: false,
    args: [
      '--start-maximized',
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'zh-CN',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  // Remove webdriver detection
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  const page = await context.newPage();

  // Step 1: Navigate
  console.log('[1] 正在打开小红书...');
  try {
    await page.goto('https://www.xiaohongshu.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
    console.log('    小红书已打开');
  } catch (e) {
    console.log('    页面加载较慢，继续等待...');
    await page.waitForTimeout(5000);
  }

  // Step 2: Wait for login
  console.log('\n[2] 请在浏览器中登录小红书');
  console.log('    登录后脚本会自动检测并继续搜索...');
  console.log('    （超时时间：5分钟）\n');

  let loggedIn = false;
  let waitCount = 0;
  const maxWait = 100; // 100 * 3s = 5 min

  while (!loggedIn && waitCount < maxWait) {
    await page.waitForTimeout(3000);
    waitCount++;

    try {
      const url = page.url();
      const hasFeed = await page.$('.note-item, [class*="note"], .explore-feed, .feeds-section');
      const hasLoginModal = await page.$('.login-container, .login-modal, [class*="qrcode"], [class*="login-input"]');
      
      // Check if we're past login (feed visible, no login modal)
      if (hasFeed && !hasLoginModal) {
        loggedIn = true;
        console.log('    ✓ 检测到已登录！');
      } else if (waitCount % 10 === 0) {
        console.log(`    等待登录中... (${waitCount * 3}s)`);
      }
    } catch (e) {
      // ignore
    }
  }

  if (!loggedIn) {
    console.log('\n⚠ 未检测到登录状态，尝试直接搜索...');
  }

  // Step 3: Search
  console.log('\n[3] 开始搜索博主...');
  const bloggerData = [];

  for (const keyword of SEARCH_KEYWORDS) {
    console.log(`\n  搜索: "${keyword}"`);
    const searchUrl = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(keyword)}&source=web_explore_feed`;
    
    try {
      await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (e) {
      console.log('    页面加载超时，重试...');
      await page.waitForTimeout(5000);
    }
    
    await page.waitForTimeout(4000);

    // Screenshot
    const safeName = keyword.replace(/[\s/]+/g, '_');
    try {
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `search_${safeName}.png`),
        fullPage: false
      });
      console.log(`    截图: search_${safeName}.png`);
    } catch (e) {
      console.log(`    截图失败: ${e.message.substring(0, 60)}`);
    }

    // Find notes and extract author info
    try {
      const noteLinks = await page.$$('a[href*="/explore/"], a[href*="/discovery/item/"]');
      console.log(`    找到 ${noteLinks.length} 条笔记`);

      for (let i = 0; i < Math.min(3, noteLinks.length); i++) {
        try {
          await noteLinks[i].click();
          await page.waitForTimeout(3000);

          // Get author name
          const authorEl = await page.$('[class*="author"] [class*="name"], .user-info .name, [class*="user-name"], .note-author .name');
          let authorName = null;
          if (authorEl) {
            authorName = (await authorEl.textContent()).trim();
          }

          if (authorName) {
            console.log(`    博主: ${authorName}`);
            
            // Try to go to author profile
            const authorLink = await page.$('a[href*="/user/profile/"], [class*="author"] a, .user-info a');
            if (authorLink) {
              const href = await authorLink.getAttribute('href');
              if (href && href.includes('/user/profile/')) {
                await authorLink.click();
              } else {
                const profileUrl = `https://www.xiaohongshu.com/user/profile/${href}`;
                await page.goto(profileUrl, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
              }
              await page.waitForTimeout(4000);

              // Screenshot profile
              const fname = `profile_${authorName.replace(/[^\w\u4e00-\u9fa5]/g, '_')}.png`;
              await page.screenshot({
                path: path.join(SCREENSHOT_DIR, fname),
                fullPage: false
              }).catch(() => {});
              console.log(`    主页截图: ${fname}`);

              // Extract profile text
              const profileText = await page.evaluate(() => {
                return document.body.innerText.substring(0, 2000);
              }).catch(() => '');

              bloggerData.push({
                name: authorName,
                keyword: keyword,
                screenshot: fname,
                profileText: profileText.substring(0, 500)
              });

              await page.goBack({ waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
              await page.waitForTimeout(2000);
            }
          }

          await page.keyboard.press('Escape').catch(() => {});
          await page.waitForTimeout(1000);
        } catch (e) {
          console.log(`    结果 ${i+1} 出错: ${e.message.substring(0, 60)}`);
        }
      }
    } catch (e) {
      console.log(`    搜索出错: ${e.message.substring(0, 80)}`);
    }
  }

  // Step 4: Search known bloggers
  console.log('\n[4] 搜索已知博主...');
  for (const blogger of KNOWN_BLOGGERS) {
    console.log(`\n  搜索: "${blogger}"`);
    const searchUrl = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(blogger)}&source=web_explore_feed`;
    
    try {
      await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (e) {
      await page.waitForTimeout(5000);
    }
    
    await page.waitForTimeout(4000);

    const safeName = blogger.replace(/[\s/]+/g, '_');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, `search_blogger_${safeName}.png`),
      fullPage: false
    }).catch(() => {});
    console.log(`    截图: search_blogger_${safeName}.png`);

    // Try to find user profile link
    try {
      const userLinks = await page.$$('a[href*="/user/profile/"]');
      if (userLinks.length > 0) {
        await userLinks[0].click();
        await page.waitForTimeout(4000);
        
        const fname = `profile_${safeName}.png`;
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, fname),
          fullPage: false
        }).catch(() => {});
        console.log(`    主页截图: ${fname}`);

        const profileText = await page.evaluate(() => {
          return document.body.innerText.substring(0, 2000);
        }).catch(() => '');

        bloggerData.push({
          name: blogger,
          screenshot: fname,
          profileText: profileText.substring(0, 500)
        });
      } else {
        console.log('    未找到用户主页链接');
      }
    } catch (e) {
      console.log(`    出错: ${e.message.substring(0, 60)}`);
    }
  }

  // Step 5: Save data
  console.log('\n[5] 保存数据...');
  const dataPath = path.join(DATA_DIR, 'blogger-search-results.json');
  fs.writeFileSync(dataPath, JSON.stringify(bloggerData, null, 2), 'utf-8');
  console.log(`    数据: references/blogger-search-results.json`);
  console.log(`    博主数: ${bloggerData.length}`);

  const screenshots = fs.readdirSync(SCREENSHOT_DIR).filter(f => f.endsWith('.png'));
  console.log(`\n=== 完成 ===`);
  console.log(`截图: ${screenshots.length} 个`);
  screenshots.forEach(f => console.log(`  references/screenshots/${f}`));

  console.log('\n浏览器 10 秒后关闭...');
  await page.waitForTimeout(10000);
  await browser.close();
  console.log('已关闭');
})();
