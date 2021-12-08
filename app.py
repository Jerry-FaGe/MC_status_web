from flask import Flask, request, render_template
from McStatus.McStatus import McStatus

app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    return 'Hello World!'


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        preset = request.form['preset']
        server_add = request.form['server']
        if not preset and not server_add:
            return '你啥也没输你想查啥？输入框和预设至少要有一个'
        if preset:
            server_add = preset
        server = McStatus.lookup(server_add)
        server_info, server_host = server.get_by_mcstatus()
        return render_template('answer.html', server_info=server_info, server_host=server_host)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
