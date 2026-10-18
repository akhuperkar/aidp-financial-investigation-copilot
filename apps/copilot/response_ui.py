"""Presentation only: never execute SQL, HTML, or code returned by an agent."""
import math
from urllib.parse import urlsplit
import altair as alt
import pandas as pd
import streamlit as st
from response_view import parse_response, chart_frame


def render_reply(turn,kind,paths):
    provider='AIDP' if kind=='aidp' else 'PAF'
    raw=turn.get('raw')
    if turn.get('error'):
        st.error(turn['error']); return
    parsed=parse_response(raw,**paths)
    elapsed=turn.get('elapsed')
    if elapsed is not None: st.caption(f'Response time · {elapsed:.2f} s (client measured)')
    if parsed['failed']:
        st.error(f'{provider} reported an unsuccessful result. Inspect the returned details below.')
    rows=parsed['rows']
    view='Narrative'
    if kind=='dataAnalysis' or rows:
        view=st.radio('Response view',['Narrative','Table','Visualization'],horizontal=True,key='view_'+turn['id'])
    if view=='Narrative':
        if parsed['text']:
            st.markdown('#### Answer')
            st.markdown(parsed['text'])
        elif rows:
            st.info(f'{provider} returned {len(rows)} row(s). Select Table or Visualization to explore them; no narrative was returned.')
        else:
            st.info('No recognized answer text. Expand Raw response and configure the Answer JSON path if needed.')
    elif view=='Table':
        if rows:
            frame=pd.DataFrame(rows)
            st.dataframe(frame,hide_index=True,width='stretch')
            st.caption(f'{len(frame)} returned row(s) · No additional query or aggregation')
        else: st.info('No structured rows returned. Use Narrative, or configure Data rows JSON path from the raw response.')
    else:
        if not rows:
            st.info('No structured rows returned for visualization. Narrative text is not converted into invented data.')
        else:
            frame=pd.DataFrame(rows)
            numeric=[c for c in frame.columns if all(isinstance(r.get(c),(int,float)) and not isinstance(r.get(c),bool) and math.isfinite(r[c]) for r in rows)]
            dimensions=[c for c in frame.columns if all(isinstance(r.get(c),(str,int,float)) and not isinstance(r.get(c),bool) for r in rows)]
            if not numeric or len(dimensions)<2:
                st.info('A chart needs a numeric measure and another usable column. Use Table for this result.')
            else:
                categories=[c for c in dimensions if c not in numeric]
                x=st.selectbox('X axis',dimensions,index=dimensions.index((categories or dimensions)[0]),key='x_'+turn['id'])
                ys=[c for c in numeric if c!=x]
                if not ys:
                    st.info('Choose a different X column to enable a numeric Y measure.')
                else:
                    y=st.selectbox('Y measure',ys,key='y_'+turn['id'])
                    shape=st.selectbox('Chart type',['Bar','Line','Scatter'],key='shape_'+turn['id'])
                    data=chart_frame(rows,x,y)
                    if data is None:
                        st.info('Selected columns contain unsupported or missing values. Use Table.')
                    elif shape=='Bar' and data[x].duplicated().any():
                        st.info('X values repeat. Select Scatter or another X column; the app does not silently sum or average rows.')
                    else:
                        if len(data)==1: st.info('Only one row was returned. This chart cannot show a trend or other months.')
                        data=data.copy(); data['_paf_row_order']=range(len(data))
                        x_type='quantitative' if x in numeric else 'nominal'
                        chart=alt.Chart(data).encode(x=alt.X(field=x,type=x_type,sort=None),y=alt.Y(field=y,type='quantitative'),
                            tooltip=[alt.Tooltip(field=x,type=x_type),alt.Tooltip(field=y,type='quantitative')])
                        if shape=='Bar': chart=chart.mark_bar(color='#4263b8')
                        elif shape=='Line':
                            chart=chart.mark_line(point=True,color='#4263b8').encode(order=alt.Order(field='_paf_row_order',type='quantitative'))
                            st.caption('Line connects rows in returned order. Use only when that order is meaningful.')
                        else: chart=chart.mark_circle(size=85,color='#4263b8')
                        st.altair_chart(chart.properties(height=300),width='stretch')
                        st.caption(f'{len(data)} returned row(s) · X: {x} · Y: {y}')
                        with st.expander('Chart values'):
                            st.dataframe(data[[x,y]],hide_index=True,width='stretch')
    if parsed['sources']:
        with st.expander(f'Sources and retrieval metadata ({len(parsed["sources"])})'):
            st.caption(f'Source fields and scores are shown as returned by {provider}. A score or distance is not a calibrated answer-confidence percentage.')
            for i,source in enumerate(parsed['sources'],1):
                if isinstance(source,dict):
                    title=source.get('title') or source.get('filename') or source.get('documentName') or source.get('source') or f'Source {i}'
                    st.write(f'{i}. {title}')
                    url=source.get('url') or source.get('source_url')
                    try:
                        valid_url = isinstance(url,str) and urlsplit(url).scheme in ('http','https') and bool(urlsplit(url).hostname)
                    except ValueError:
                        valid_url = False
                    if valid_url:
                        st.link_button('Open source',url)
                    st.json(source)
                else: st.write(f'{i}. {source}')
    elif kind=='knowledge':
        st.caption('No structured citations or retrieval scores were returned or recognized. Any inline references remain in the answer.')
    if parsed['metadata']:
        with st.expander(f'Additional metadata returned by {provider}'):
            st.json(parsed['metadata'])
            st.caption(f'Original field names and values; timing units and score semantics depend on {provider}.')
    if parsed['query']:
        with st.expander(f'SQL returned by {provider}'):
            st.code(parsed['query'],language='sql')
            st.caption('Displayed for inspection only; the Streamlit app does not execute this SQL.')
    with st.expander('Raw response'):
        st.json(raw)
        if turn.get('request')!=turn.get('prompt'):
            st.caption(f'Message sent to {provider}, including the optional formatting instruction:')
            st.code(turn.get('request',''),language=None)
