TUN device setup commands

```
sudo openvpn --mktun --dev tun13
sudo ip link set tun13 up
sudo ip addr add 10.0.0.1/24 dev tun13
```

scanimage -d 'pixma:04A918A2_6F937A' -p -o test.pdf --format pdf --resolution 300

