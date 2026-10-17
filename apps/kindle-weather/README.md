# Kindle Weather

For the 2012 Kindle Paperwhite (5th generation), firmware 5.6.1.1, use:

**http://192.168.1.100:30080/**

The active Rollouts Service exposes NodePort 30080. The app's LAN NetworkPolicy
permits `192.168.1.0/24` on target port 8080. The preview Service remains private,
and the public HTTPS endpoint uses the same active revision through Istio.
Do not forward port 30080 from the internet.

Layout regression tests live in `joekleinsorge/kindle-weather` and run before
container publication. They cover Paperwhite viewports with browser controls,
the photographed tide-time overlap, wider times, CSS/fonts, and ordinary
navigation with JavaScript disabled. Modern WebKit cannot reproduce every
firmware 5.6.1.1 behavior, so check the physical Kindle after layout changes.

Deploy a tested image by updating the pinned digest in `deployment.yaml` and
letting Argo CD reconcile it. Confirm that the blue-green Rollout is healthy,
HTTP and HTTPS return the new CSS version, and the tide time and chart remain
separate on the Kindle. A rollback restores the previous image digest in Git.
