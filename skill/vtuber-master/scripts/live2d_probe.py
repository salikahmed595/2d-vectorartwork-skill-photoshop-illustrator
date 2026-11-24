#!/usr/bin/env python3
"""Passive Live2D Cubism Editor local external API availability probe."""
import argparse, asyncio, json, sys, uuid

async def main(port):
    try:
        import websockets
    except ImportError:
        print('Install dependency: python -m pip install websockets')
        return 2
    uri=f'ws://127.0.0.1:{port}'
    try:
        async with websockets.connect(uri, open_timeout=5) as ws:
            req={'Version':'1.0.0','Type':'Request','RequestId':str(uuid.uuid4()),'Method':'RegisterPlugin','Data':{'Name':'VTuber Master Local Probe'}}
            await ws.send(json.dumps(req))
            raw=await asyncio.wait_for(ws.recv(), timeout=10)
            response=json.loads(raw)
            print(json.dumps({'connected':True,'type':response.get('Type'),'method':response.get('Method'),'authorization_may_be_required':True}, indent=2))
            print('Check Cubism External Application Integration Settings and Allow trusted app. Connection alone cannot rig a model.')
            return 0
    except Exception as e:
        print(f'Could not connect to Cubism at {uri}: {type(e).__name__}: {e}')
        print('Open Cubism Editor, enable External Application Integration and keep remote access disabled.')
        return 1

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=22033)
    args=parser.parse_args()
    sys.exit(asyncio.run(main(args.port)))
