# IPoPS - Internet Protocol over Postal Services

*HackNotts 2025 entry*

---

[IP over Avian Carriers](https://en.wikipedia.org/wiki/IP_over_Avian_Carriers), while a noble proposition, is wholly inappropriate for usage in the modern day. It is unreliable, vulnerable to attacks and is untrackable. Instead, we propose IPoPS - IP over Postal Services - to facilitate your inter-machine communications with complete peace of mind.

## What it does

IPoPS provides a TUN device for your Linux-based computer, the same technology used to implement VPNs. All traffic received by the TUN device is encoded in our state-of-the-art data-matrix-based scheme and printed onto A4 sheets.

Such sheets may then be posted to the intended recipient that is also running IPoPS. They are able to scan the sheets, have them read and sequentially re-ordered automatically, and forwarded on to the correct process.

Postal services are an ideal transport for IP data - thanks to robust, pre-existing legislation that exists to secure the postal service in most countries (for example, it is illegal to open the mail of another person), as well as the option for tracked postage and a variety of cost-vs-speed options, virtually all needs are well-served by IPoPS.

## How we built it

Four parts:

* A printer (we didn't build this part)
* A [TUN](https://en.wikipedia.org/wiki/TUN/TAP) driver written in C
* A Python printing client that generates printed documents
* A Python scanning client that retrieves data from printed documents

## Challenges we ran into

* The printer we bought with us sprang a leak during transport and stopped working, so we spent the first 2 hours buying a new printer
  * May it also be noted that Canon does not provide arm64 printer drivers
* Networking is hard
* the linux kernel was mean to us :(
* Data matrices don't let you encode null bytes
* ~~Somewhere along the line there's a messy data corruption bug~~ NOT ANY MORE HAHAH
* At one point I managed to screw up my networking config enough that I had to restart
 
## Accomplishments that we're proud of

IT WORKSSSSSS!!!!!

## What we learned

Not only are printers evil, but so is networking! By sheer coincidence, it even works underwater...
 
## What's next for IPoPS
 
the bin? and/or a SIGBOVIK paper
