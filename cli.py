"""Simple CLI client for interacting with the KV HTTP API."""
import argparse, requests, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base server URL')
    sub = parser.add_subparsers(dest='cmd')
    p_put = sub.add_parser('put'); p_put.add_argument('key'); p_put.add_argument('value'); p_put.add_argument('--ttl', type=float)
    p_get = sub.add_parser('get'); p_get.add_argument('key')
    p_del = sub.add_parser('del'); p_del.add_argument('key')
    p_add = sub.add_parser('addrep'); p_add.add_argument('url')
    p_list = sub.add_parser('listrep')
    args = parser.parse_args()

    if args.cmd == 'put':
        url = f"{args.url}/kv/{args.key}"
        params = {}
        if args.ttl: params['ttl'] = str(args.ttl)
        r = requests.put(url, data=args.value.encode('utf-8'), params=params)
        print(r.json())
    elif args.cmd == 'get':
        url = f"{args.url}/kv/{args.key}"
        r = requests.get(url)
        if r.status_code == 200:
            print(r.content.decode('utf-8', errors='replace'))
        else:
            print('NOT FOUND', file=sys.stderr); sys.exit(2)
    elif args.cmd == 'del':
        url = f"{args.url}/kv/{args.key}"
        r = requests.delete(url)
        print(r.json())
    elif args.cmd == 'addrep':
        url = f"{args.url}/admin/replicas"
        r = requests.post(url, json={'url': args.url})
        print(r.json())
    elif args.cmd == 'listrep':
        url = f"{args.url}/admin/replicas"
        r = requests.get(url)
        print(r.json())
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
