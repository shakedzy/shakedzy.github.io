import os
import pathlib
from datetime import datetime
from PIL import Image, ExifTags
from typing import List


CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
PHOTO_GALLERY = "photo-gallery"
PHOTOS = "photos"

HTML_BEGINNING = """
<!DOCTYPE HTML>
<!--
	Multiverse by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
-->
<html>
	<head>
        <meta name="author" content="Shaked Zychlinski">
        <meta property="og:type" content="website">
        <meta property="og:title" name="title" content="This Is Me">
        <meta property="og:description" name="description" content="Hey there, welcome!">
        <meta property="og:url" content="https://shakedzy.xyz">
        <meta property="og:image:type" content="image/png">
        <meta property="og:image:width" content="640">
        <meta property="og:image:height" content="360">

        <meta property="og:image" content="https://shakedzy.xyz/images/social_banner.png">
        <meta property="og:image:secure_url" content="https://shakedzy.xyz/images/social_banner.png" />
        <meta name="twitter:image" content="https://shakedzy.xyz/images/social_banner.png">

        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:site" content="https://shakedzy.xyz">
        <meta name="twitter:creator" content="@shakedzy">
        <meta name="twitter:title" content="This Is Me">
        <meta name="twitter:description" content="Hey there, welcome!">


		<title>This is me: shakedzy</title>
        <link rel="shortcut icon" type="image/png" href="https://shakedzy.xyz/favicon.png">
		<meta charset="utf-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
		<link rel="stylesheet" href="assets/css/main.css" />
		<noscript><link rel="stylesheet" href="assets/css/noscript.css" /></noscript>
	</head>
	<body class="is-preload">

		<!-- Wrapper -->
			<div id="wrapper">

				<!-- Header -->
					<header id="header">
						<h1><a href="https://shakedzy.xyz"><strong>This Is Me</strong>: My Photo Gallery</a></h1>
						<nav>
							<ul>
								<li><a href="#footer" class="icon solid fa-info-circle">About</a></li>
							</ul>
						</nav>
					</header>

				<!-- Main -->
					<div id="main">
"""
HTML_END = """
					</div>

				<!-- Footer -->
					<footer id="footer" class="panel">
						<div class="inner split">
							<div>
								<section>
									<h2>My Photo Gallery</h2>
									<p>Some photos are available on <a href="https://shutterstock.com/g/shakedzy">ShutterStock</a></p>
								</section>
								<p class="copyright">
									&copy; Shaked Zychlinski. Design: <a href="http://html5up.net">HTML5 UP</a>.
								</p>
							</div>
						</div>
					</footer>

			</div>

		<!-- Scripts -->
			<script src="assets/js/jquery.min.js"></script>
			<script src="assets/js/jquery.poptrox.min.js"></script>
			<script src="assets/js/browser.min.js"></script>
			<script src="assets/js/breakpoints.min.js"></script>
			<script src="assets/js/util.js"></script>
			<script src="assets/js/main.js"></script>

	</body>
</html>
"""
HTML_SINGLE_PHOTO = """
						<article class="thumb">
							<a href="{photo}" class="image"><img src="{photo}" alt="" /></a>
						</article>
"""


def get_image_time(photo_filename: str) -> float:
    _, _, date, time, _ = photo_filename.split('-')
    return datetime.strptime(f'{date} {time}', '%y%m%d %H%M%S').timestamp()


def run():
    photos_dir = os.path.join(CURRENT_DIR, PHOTO_GALLERY, PHOTOS)
    photos: List[str] = [name for name in os.listdir(photos_dir) if name.endswith('.jpg')]
    ordered_photos = sorted(photos, key=lambda x: -get_image_time(x))
    with open(os.path.join(CURRENT_DIR, PHOTO_GALLERY, 'gallery.html'), 'w') as html:
        html.write(HTML_BEGINNING)
        for photo in ordered_photos:
            html.write(HTML_SINGLE_PHOTO.format(photo=os.path.join(PHOTOS, photo)))
        html.write(HTML_END)

if __name__ == '__main__':
    run()
