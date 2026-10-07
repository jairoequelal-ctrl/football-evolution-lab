import base64
from .pipeline import ROOT

def brand(fig):
    logo=base64.b64encode((ROOT/'assets/statsbomb-logo.png').read_bytes()).decode()
    fig.add_layout_image(source='data:image/png;base64,'+logo,xref='paper',yref='paper',x=1,y=1.16,sizex=.16,sizey=.13,xanchor='right',yanchor='top',sizing='contain')
    fig.add_annotation(text='Data: StatsBomb Open Data · cobertura parcial',xref='paper',yref='paper',x=0,y=-.2,showarrow=False,font=dict(size=11))
    fig.update_layout(margin=dict(t=90,b=100),paper_bgcolor='#160f29',plot_bgcolor='#160f29',font=dict(color='#faf8fd'),colorway=['#ff428e','#76d5f4','#a78bfa','#ffbe76'])
    return fig
