const app = require('express')();
const bodyParser = require('body-parser');
const puppeteer = require('puppeteer');
app.post('/', bodyParser.json(), async (req, res) => {
	console.log(req.body);
	res.send(await search(10, req.body.fname));
});

app.listen(6175);

async function foolGoogle(waiter) {
	const page = await waiter;

	await page.setViewport({width: 800, height: 600,});
	await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.39 Safari/537.36');
	await page.evaluateOnNewDocument(() => {
		window.navigator.chrome = {runtime: {}};
		Object.defineProperty(navigator, 'webdriver', {get: () => false});
		Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
		Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

	});
	await page.evaluateOnNewDocument(() => (
		window.navigator.permissions.query = async (param) => (
			param.name === 'notifications' ?
			{ state: Notification.permission } :
			window.navigator.permissions.query(param)
		)
	));
	return page;
}

async function discardResources(waiter) {
	const page = await foolGoogle(waiter);

	await page.setRequestInterception(true);
	page.on('request', req => {
		switch (req.resourceType()) {
			case 'stylesheet':
			case 'image':
			case 'font':
				req.abort();
				break;
			default:
				req.continue();
		}
	});
	return page;
}

async function search(n, imgName) {
	const startTime = process.hrtime();
	const counter = Array.from({length: n}, (_, i) => i);

	const browser = await puppeteer.launch({
		// executablePath: '/usr/bin/chromium-browser',
		args: [
			'--disable-dev-shm-usage',
			'--no-sandbox',
		],
	});
	const waiters = counter.map(_ => discardResources(browser.newPage()));
	const page0 = await foolGoogle(browser.newPage());

	await Promise.all([
		page0.waitForNavigation(),
		page0.goto('https://images.google.com/imghp?sbi=1'),
	]);
	await Promise.all([
		page0.waitForNavigation(),
		(await page0.$('#qbfile')).uploadFile(imgName),
	]);
	await Promise.all([
		page0.waitForNavigation(),
		page0.click('a.iu-card-header'),
	]);

	const rawLinks = await Promise.all(counter.map(i =>
		page0.$eval(`div[data-ri="${i}"]`, div => [
			div.getElementsByTagName('img')[0].src,
			div.getElementsByTagName('a')[0].href,
		])
	));
	await page0.close();
	const links = await Promise.all(rawLinks.map(async (rawLink, i) => {
		const [src, origin] = rawLink;
		const page = await waiters[i];
		const [atag, _] = await Promise.all([
			page.waitForSelector('a.irc_pt[tabindex="0"]'),
			page.goto(origin),
		]);
		const href = await page.evaluate(a => a.href, atag);
		page.close();
		return [src, href];
	}));

	const duration = process.hrtime(startTime);
	const sec = duration[0];
	const msec = parseInt(duration[1] / 1000000);
	const timeMsg = `Search took ${sec}.${msec} seconds.`;
	console.log(timeMsg);
	await browser.close();
	
	return [
		`<p>${timeMsg}</p><div id="gallery">`,
		...links.map(([src, href]) =>
			`<a href="${href}" target="_blank"><img src="${src}"></a>`
		),
		'</div>',
	].join('');
}
