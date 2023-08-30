About
==========

- Simple vpn in `python`
- Client + server
- Client routes all its traffic through `tun`
- Uses `websockets` as transport
- Can be used behind nginx for ssl
- No custom encryption, but builtin `tls` if websockets connection was established over `HTTPS` via nginx
- No authorization
- **linux only**

Inspired by [this vpn demo in c by davlxd](https://github.com/davlxd/simple-vpn-demo)

also good read: [simpletun](http://backreference.org/2010/03/26/tuntap-interface-tutorial/)

Usage
=====================

client and server must run with **sudo** so dependencies must be installed as **sudo**
```
sudo python3 install -r requirements.txt
````

Run server
==========

```
sudo python3 server.py
```

Run client
==========

```
sudo python3 client.py
```

