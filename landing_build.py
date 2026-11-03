"""Export the landing page artboard (Design canvas .dc.html) to landing/index.html."""
import re, sys
src = open(sys.argv[1]).read()
assert '{{' not in src
title = re.search(r'<title>(.*?)</title>', src).group(1)
helmet = re.search(r'<helmet>(.*?)</helmet>', src, re.S).group(1)
body = re.search(r'</helmet>(.*?)</x-dc>', src, re.S).group(1)
for blob, local in [('/_blob/fe704cd5d4e781daad88495d835da011', 'qr.png'),
                    ('/_blob/543ad5a368d9e71f5e9ebd9f443a967b', 'demo.mp4'),
                    ('/_blob/ef68f50cb913e510ded9461f16e6dcac', 'poster.jpg')]:
    body = body.replace(blob, local)
assert '/_blob/' not in body
body = body.replace('href="https://zkrypy.github.io/foodQ/#client"', 'href="../"')
html = f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="FoodQ: đặt món trước, thanh toán VietQR, theo dõi số thứ tự và nhận món đúng lúc.">
{helmet.strip()}
<style>html{{scroll-behavior:smooth}}h1{{font-size:clamp(40px,8vw,60px)!important}}h2{{font-size:clamp(28px,5vw,38px)!important}}</style>
</head>
<body>{body}</body>
</html>
'''
open('landing/index.html', 'w').write(html)
print('landing/index.html', len(html))
