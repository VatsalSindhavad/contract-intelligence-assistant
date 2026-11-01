import json
import sys


def main():
    import torch
    from dense_retrieval import LocalEncoder
    config=json.loads(sys.argv[1])
    encoder=LocalEncoder(config)
    print(json.dumps(dict(ready=True)),flush=True)
    for line in sys.stdin:
        try:
            request=json.loads(line)
            if request['operation']=='encode':
                result=encoder.encode(request['texts']).tolist()
            elif request['operation']=='lengths':
                result=encoder.token_lengths(request['texts'])
            else:
                raise ValueError('Unsupported embedding operation.')
            reply=dict(result=result)
        except Exception as error:
            reply=dict(error=type(error).__name__+': '+str(error))
        print(json.dumps(reply,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
