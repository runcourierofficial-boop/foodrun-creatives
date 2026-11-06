# Food Run creative pipeline (used by the Creative Agent)

Setup in a fresh session:
    gh repo clone runcourierofficial-boop/foodrun-creatives /home/claude/foodrun-creatives
    cd /home/claude/foodrun-creatives/tools && pip list 2>/dev/null | grep -i pillow   # PIL + ffmpeg are preinstalled

Generate image creatives (1:1 + 9:16) for every deal in deals.json:
    python3 -I creative_gen.py deals.json photos out
Build a Reels slideshow from 9x16 cards:
    python3 -I video_gen.py out "zinger549,pizzarun699,triplecrunch2399" out/reel_evening.mp4 3
Get a new dish photo from the website (900x900): open https://foodrun.store/uploads/dishes/<uuid>.jpg
    (find the uuid from the product card's next/image ?url= param on foodrun.store), or use Chrome screenshot + stitch.py.

Rules: every title/price/sub must match foodrun.store exactly. "Cash on delivery" and "Open 24 hours" are owner-approved claims.
Publish: copy out/*.jpg|mp4 into ../img or ../video, git add/commit/push → Meta fetches
https://raw.githubusercontent.com/runcourierofficial-boop/foodrun-creatives/main/img/<file>
