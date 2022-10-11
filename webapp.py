import tempfile
from flask import Flask, request, flash, render_template
from werkzeug.utils import secure_filename
import logging 
logging.basicConfig(level=logging.DEBUG)
l=logging.getLogger(__name__)

import os
from classes import DataPoint, SenderMaker,  Parser

app=Flask(__name__) 
app.debug=os.environ.get('APP_DEBUG', False)
app.config['UPLOAD_FOLDER']=os.environ.get('UPLOADS', '/tmp')
app.config['OUTPUT_FOLDER']=os.environ.get('OUTPUTS')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method=='GET':
        return render_template('main.html', mode="upload")

    ## POST
    f=request.files['file']
    sf=secure_filename(f.filename)
    f.save(sf)
    try:
        p=Parser(sf)
        datapoints=DataPoint.fromlist(p.packets)
        for d in datapoints.values():
            d.makestats(p.senders)
        sm=SenderMaker(datapoints, p)
        sm.score()
        cons=[]
        for d in datapoints.values():
            cons=cons+d.stats.consensus
        best_senders=sorted(sm.senderlist, key=lambda x: x.score, reverse=True)[:2]
        outdir=tempfile.mkdtemp(dir=app.config['OUTPUT_FOLDER'], prefix='sender_report_')
        l.info(f"outdir: {outdir}")
    except Exception as e:
        return render_template('main.html', error=str(e))
    
    result=render_template('main.html', mode='result', 
        senders=sm.senderlist, 
        charts=[(label, chart) for label, chart in sm.charts.items()], 
        best_senders=best_senders, consensus=cons, outdir=outdir)
    
    with open(f"{outdir}/sender_report.html", 'w') as f:
        f.write(result)
    return result
    


if __name__=='__main__':
    app.run()
