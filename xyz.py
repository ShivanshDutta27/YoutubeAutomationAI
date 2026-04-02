


CHANNEL_ID = "UCw8Ut_9D4MM4yLx3n4HjXRQ"

videos = get_videos(CHANNEL_ID)

print("\n=== VIDEOS ===")
for v in videos:
    print(v)
    

video_ids = [v["video_id"] for v in videos]

stats = get_video_stats(video_ids)

print("\n=== STATS RAW ===")
print(stats)

print("\n=== CLEAN STATS ===")
for item in stats["items"]:
    print({
        "video_id": item["id"],
        "views": item["statistics"].get("viewCount"),
        "likes": item["statistics"].get("likeCount"),
        "comments": item["statistics"].get("commentCount"),
    })



test_video_id = videos[0]["video_id"]

comments = get_comments(test_video_id)

print("\n=== COMMENTS ===")
for i, c in enumerate(comments[:10]):
    print(f"{i+1}. {c}")