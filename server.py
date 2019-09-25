import os
import re
import threading
from collections import defaultdict

import shutil
import requests
import json
import base64

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
from tornado.options import define, options
from tornado.httputil import parse_multipart_form_data

from landslide import parser2
from road_detection import road_detection
from request_cofact_utils import run_query
from Abusiveword import AbusiveWordDetection
from url_detection import url_detection
from lstm_live import lstm_model

define("port", default=6174, help="run on the given port", type=int)

class AtomicCounter:
    """
    An atomic counter that cycles through 0 to n-1 indefinitely.
    """
    def __init__(self, n):
        self._value = 0
        self._n = n
        self._lock = threading.Lock()
    
    def pop(self):
        with self._lock:
            value = self._value
            self._value = (value + 1) % self._n
            return value

counter = AtomicCounter(10000000)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")

class ImageHandler(tornado.web.RequestHandler):
    def boundary(self):
        content_type = self.request.headers['Content-Type']
        bb = content_type.rfind('boundary=')
        boundary = bytes(content_type[bb + 9:], 'utf-8')
        return boundary

    def post(self):
        arguments = {}
        files = {}
        parse_multipart_form_data(self.boundary(), self.request.body, arguments, files)
        fname = f'img/{counter.pop()}'
        print('filename:', fname)
        
        try:
            img_url = None
            img_file = None
            img_selector = tornado.escape.to_unicode(arguments['img-selector'][0])

            if not img_selector:
                self.write('you send no image')
                return
            
            print('should be:', img_selector)
            print('turned out to be:', end=' ')
            if img_selector == 'img-url':
                img_url = tornado.escape.to_unicode(arguments['img-url'][0])
                if not img_url:
                    raise Exception('empty img_url')
                if img_url[:5] == 'data:':
                    comma = img_url.find(',')
                    if comma < 0:
                        raise Exception('invalid base64')
                    else:
                        print('base64 image')
                        with open(fname, 'wb') as fout:
                            fout.write(base64.decodebytes(img_url[comma + 1:].encode()))
                else:
                    try:
                        print('url found')
                        r = requests.get(img_url, stream=True)
                        with open(fname, 'wb') as fout:
                            shutil.copyfileobj(r.raw, fout)
                        del r
                    except:
                        raise Exception('img_url download failed')
            elif img_selector == 'img-file':
                img_file = files['img-file'][0]['body']
                print('file found')
                with open(fname, 'wb') as fout:
                    fout.write(img_file)
            elif img_selector == 'img-drop':
                img_drop = files['img-drop'][0]['body']
                print('drop found')
                with open(fname, 'wb') as fout:
                    fout.write(img_drop)
            else:
                raise Exception('invalid img_selector')
        except Exception as err:
            print(f'Error occurred: {err}')
            self.write(str(err))
            return
        
        b64img = None
        with open(fname, 'rb') as fin:
            b64img = base64.b64encode(fin.read()).decode('ascii')
#             self.write(f'<img id="original" src="data:;base64,{b64img}">')
        
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = {'fname': fname}
        res = requests.post(
            'http://localhost:6175/',
            data = json.dumps(data),
            headers = headers
        )
        self.write(f'<img id="original" src="data:;base64,{b64img}">{res.text}')
        
        try:
            os.remove(fname)
        except:
            pass

class NewsHandler(tornado.web.RequestHandler):
    def boundary(self):
        content_type = self.request.headers['Content-Type']
        bb = content_type.rfind('boundary=')
        boundary = bytes(content_type[bb + 9:], 'utf-8')
        return boundary

    def post(self):
        arguments = {}
        files = {}
        parse_multipart_form_data(self.boundary(), self.request.body, arguments, files)
        raw_content = ''
        raw_title = ''
        raw_url = ''
        try:
            raw_content = tornado.escape.to_unicode(arguments['content'][0])
            raw_title = tornado.escape.to_unicode(arguments['title'][0])
            raw_url = tornado.escape.to_unicode(arguments['url'][0])
        except:
            print('Error occurred while parsing arguments.')
            pass
        
        result_url = 'URL is empty'
        if raw_url:
            result_url = (
                f'We got your url: <a href="{raw_url}">{raw_url}</a>,<br>'
                'but the url detection feature is temporarily unavailable '
                'due to dependency problems.'
            )
        result_url = url_detection(raw_url)
        result_cofacts = []
        result_road_title = []
        if raw_title:
            result_cofacts = run_query(raw_title, '10')['data']['ListArticles']['edges']
            result_road_title, _ = road_detection({
                'content':f'{raw_title}。',
                "title":raw_title,
                'datetime':'',
                'url':raw_url,
            })
            print(result_road_title)
        
        result_road_body = [[], None]
        if raw_content:
            result_road_body = road_detection({
                'content': raw_content,
                'title': raw_title,
                'datetime': '',
                'url': raw_url,
            })
        result_abuse_animal_title, result_abuse_animal_body = self.application.model["model_abuse_animal"].predict_new_server(raw_title, raw_content)
        result_fail_policy_title, result_fail_policy_body = self.application.model["model_fail_policy"].predict_new_server(raw_title, raw_content)
        result_price_up_title, result_price_up_body = self.application.model["model_price_up"].predict_new_server(raw_title, raw_content)
        result_throw_fruit_title, result_throw_fruit_body = self.application.model["model_throw_fruit"].predict_new_server(raw_title, raw_content)
        detector = AbusiveWordDetection()
        result_abusive_title = detector.title_detection(raw_title)
        result_abusive_body = detector.content_detection({
            'content': raw_content,
            'title': raw_title,
            'datetime': '',
            'url':raw_url,
        })
        self.write(tornado.escape.json_encode({
            'result-road-content': self.road_detection_body(*result_road_body),
            'result-road-title': self.road_detection_title(result_road_title[:-1]),
            'result-emotion-content': self.abusive_detection('Text', result_abusive_body),
            'result-emotion-title': self.abusive_detection('Title', result_abusive_title),
            'result-abuse-animal-content': self.waste_detection('Text', result_abuse_animal_body),
            'result-abuse-animal-title': self.waste_detection('Title', result_abuse_animal_title),
            'result-fail-policy-content': self.waste_detection('Text', result_fail_policy_body),
            'result-fail-policy-title': self.waste_detection('Title', result_fail_policy_title),
            'result-price-up-content': self.waste_detection('Text', result_price_up_body),
            'result-price-up-title': self.waste_detection('Title', result_price_up_title),
            'result-throw-fruit-content': self.waste_detection('Text', result_throw_fruit_body),
            'result-throw-fruit-title': self.waste_detection('Title', result_throw_fruit_title),
            'result-url': result_url,
            'result-correlation': self.cofacts_title(result_cofacts),
        }))
    
    def abusive_detection(self, name, result):
        text = ''
        for (s, r) in result:
            if r == 1:
                text += f'<span>{s}</span>'
            elif r == 2:
                text += f'<span class="red">{s}</span>'
            else:
                text += s
            if s in ('。', '?', '!', '？', '！'):
               text += '<br><br>'
        if not text:
            text = f'{name} is empty.'
        elif all(r not in (1, 2) for (_, r) in result):
            text = 'No result.'
        return text

    def road_detection_title(self, result):
        text = ''
        for (s, r, i) in result:
            if r == 1:
                text += f'<span>{s}</span>'
            elif r == 2:
                text += f'<span class="bold color{i}">{s}</span>'
            else:
                text += s
        if not text:
            text = 'Title is empty.'
        elif all(r not in (1, 2) for (_, r, __) in result):
            text = 'No result.'
        return text


    def price_up_detection(self, name, result):
        text = ""
        for s, r in result[0]:
            if r == 1:
                text += '<span style="background-color:yellow;">' + s + '</span>'
            elif r == 2:
                text += '<span style="color:Red;background-color:yellow;">' + s + '</span>'
            elif r == 3:
                text += '<span style="color:Red;">' + s + '</span>'
            else:
                text += s
            if s in ['。', '?', '!', '？', '！']:
                text += "<br><br>"
        if not text:
            text = f'{name} is empty.<?@!>'
        else:
            text += '<?@!>'
            for q in result[1]:
                text += q + "<br>"
        return text


    def waste_detection(self, name, result):
        text = ""
        for s, r in result[0]:
            if r == 1:
                text += '<span style="background-color:yellow;">' + s + '</span>'
            elif r == 2:
                text += '<span style="color:Red;background-color:yellow;">' + s + '</span>'
            elif r == 3:
                text += '<span style="color:Red;">' + s + '</span>'
            else:
                text += s
            if s in ['。', '?', '!', '？', '！']:
                text += "<br><br>"
        if not text:
            text = f'{name} is empty.<?@!>'
        else:
            text += '<?@!>'
            for q in result[1]:
                text += q + "<br>"
        return text
    
    def cofacts_title(self, result):
        msg = {'RUMOR':'含有不實訊息', 'NOT_ARTICLE':'不在查證範圍', 'NOT_RUMOR':'含有正確訊息'}
        text = ''
        for node in result:
            node = node['node']
            if 'text' not in node:
                continue
            inner = ''
            for reply in node["articleReplies"]:
                inner += (
                    '<h3 style="color:Green;">現有回應:</h3>'
                    f'<span class="red">{msg.get(reply["reply"]["type"], "含有個人意見")}</span><br>'
                    f'{reply["reply"]["text"]}<br><br>'
                )
            text += (
                '<h3 style="color:Blue;">訊息原文:</h3><br>'
                f'{node["text"]}<br><br>'
                f'{inner}<hr><br>'
            )
        if not text:
            text = 'No result.'
        return text.replace("\n", "<br>")
    
    def road_detection_body(self, result, extracted_table):
        text = ''
        extra = ''
        sentence_count = 0
        sentence_pos_count = 0
        pre_r = 0
        last = len(result) - 1
        for idx, (s, r, i) in enumerate(result):
            if r == 1:
                text += f'<span>{s}</span>'
            elif r == 2:
                text += f'<span class="bold color{i}">{s}</span>'
            else:
                text += s
            if (s in ('。', '?', '!', '？', '！')) or (idx == last):
                if pre_r in (1, 2):
                    sentence_pos_count += 1
                sentence_count += 1
                text += '<br><br>'
            pre_r = r
        if not result:
            text = 'text is empty.'
        elif not extracted_table:
            text = 'No result.'
        else:
            table = '<tr><th>道路</th><th>路段/里程數</th><th>地點</th><th>起始時間</th><th>截止時間</th></tr>'
            for tr in extracted_table:
                row = ''
                for td in tr:
                    row += f'<td class="{td == "None"}">{td}</td>'
                table += f'<tr>{row}</tr>'
            extra = (
                f'新聞總句數: {sentence_count}<br>'
                f'道路中斷相關句數: {sentence_pos_count}<br><br>'
                f'Extracted table:<table>{table}</table>'
            )
        if extra:
            return f'{text}<hr>{extra}'
        else:
            return text

class Application(tornado.web.Application):
    def __init__(self):
        settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "autoreload": True,
        }
        handlers = [
            (r"/", IndexHandler),
            (r"/newsDetection", NewsHandler),
            (r"/imageDetection", ImageHandler),
        ]
        self.kwargs = {}

        model_list = ["model_abuse_animal", "model_fail_policy", "model_price_up", "model_throw_fruit"]
        self.model = dict()
        for m in model_list:
            self.model[m] = lstm_model(model_path= "./models/"+m, max_sentence_length=60)
        print('all model loaded')

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    #http_server.listen(options.port, '140.112.29.242')
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
