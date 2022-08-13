from datetime import datetime
from gtts import gTTS
import praw
from bs4 import BeautifulSoup
import imgkit
from datetime import datetime
import os
import moviepy.editor as mpy
from mutagen.mp3 import MP3

# create class RedditAuthor
class RedditAuthor:
    def __init__(self, authorName : str, authorImage : str):
        self.authorName = authorName
        self.authorImage = authorImage


# create class RedditObject
class RedditObject:
    def __init__(self, topic : str, comments : list, id : str, upvotes : int, author, timestamp, nbComments, awards):
        self.id = id
        self.topic = topic
        self.comments = comments
        self.upvotes = upvotes
        self.author = author
        self.timestamp = timestamp
        self.nbComments = nbComments
        self.awards = awards

    def __str__(self):
        return self.topic + " with " + str(len(self.comments))
    
    def __repr__(self):
        return self.topic + " with " + str(len(self.comments))


# create class RedditComment
class RedditComment:
    def __init__(self, comment : str, author, upvotes : int, timestamp, obj):
        self.comment = comment
        self.author = author
        self.upvotes = upvotes
        self.timestamp = timestamp
        self.obj = obj


def readCredentials():
    with open("credentials.txt", "r") as file:
        lines = file.readlines()
        return lines[0].strip(), lines[1].strip()


def getPosts(numberOfPosts):
    postsList = []         
    redditUsername, redditPassword = readCredentials()
    reddit = praw.Reddit(client_id='HSpPGBBIzLbXoGHSUvaMnQ',
                         client_secret='nymnF7nwF8Vd8UUOARfzyE73m8etoQ',
                         user_agent='reditTTS (by /u/DenseInspection1507)',
                         username=redditUsername,
                         password=redditPassword)
    subreddit = reddit.subreddit('askReddit')
    for submission in subreddit.hot(limit=numberOfPosts):
        commentList = []
        for top_level_comment in submission.comments.list()[:10]:
            if type(top_level_comment) is praw.models.Comment and len(top_level_comment.body) > 15:
                author = RedditAuthor(top_level_comment.author.name, top_level_comment.author.icon_img)
                comment = RedditComment(top_level_comment.body, author, top_level_comment.ups, top_level_comment.created_utc, top_level_comment)
                commentList.append(comment)
        post = RedditObject(submission.title, commentList, submission.id, submission.ups, submission.author.name, submission.created_utc, submission.num_comments, submission.all_awardings)
        postsList.append(post)
        print("added post")
    return postsList


def postToSpeech(post):
    directory = "./" + post.id + "/"
    # set speed to high
    topic = gTTS(post.topic, lang="en", slow=False)
    #sox_effects = ("speed", "1.5")
    topic.save(directory + "topic.mp3")
    num = 0
    for comment in post.comments:
        speech = gTTS(comment.comment, lang="en", slow=False)
        speech.save(directory + "comment" + str(num) + ".mp3")
        num+=1


def formatUpvotes(upvotes):
    if upvotes < 1000:
        return str(upvotes)
    elif upvotes < 1000000:
        return "{:.1f}".format(upvotes / 1000) + "K"
    else:
        return "{:.1f}".format(upvotes / 1000000) + "M"


def formatTime(timestamp):
    # get time difference
    timeDiff = datetime.now() - datetime.fromtimestamp(timestamp)
    timePosted = timeDiff.total_seconds() // 3600
    print("time:", timePosted)
    return int(timePosted)


def formatPostedBy(post : RedditObject):
    return "Posted by " + post.author + "  " + str(formatTime(post.timestamp)) + " hours ago"


def generateTopicScreenShot(post : RedditObject):
    # make new directory
    directory = "./" + post.id + "/"
    if not os.path.exists(directory):
        os.makedirs(directory)

    html = open("templates/topic.html")
    soup = BeautifulSoup(html, "html.parser")
    # replace upvotes       
    upvotesTag = soup.find("p", {"class": "upvotes"})
    upvotesTag.string = str(formatUpvotes(post.upvotes))

    # replace topic
    topicTag = soup.find("p", {"class": "topic-content-text"})
    topicTag.string = post.topic
    
    # replace header
    headerTag = soup.find("p", {"class": "posted-by"})
    headerTag.string = formatPostedBy(post)

    # replace number of comments
    commentsTag = soup.find("p", {"class": "comment-text"})
    commentsTag.string = formatUpvotes(post.nbComments) + " comments"

    # replace awards
    for award in post.awards:
        awardCount = award['count']
        awardIconeURL = award['icon_url']
        # add new block of code
        if len(post.awards) == 1 and post.awards[0] == award:
            awardTag = soup.new_tag("div", attrs={"class": "float-child", "style": "margin-right:20px;"})
        else:
            awardTag = soup.new_tag("div", attrs={"class": "float-child"})
        awardTag.append(soup.new_tag("img", attrs={"src": awardIconeURL, "class": "award-icon less-margin float-child"}))
        awardCountTag = soup.new_tag("p", attrs={"class": "award-count less-margin float-child"})
        awardCountTag.string = str(awardCount)
        awardTag.append(awardCountTag)
        awardsTag = soup.find("div", attrs={"class": "topic-header"})
        awardsTag.append(awardTag)
        print("added award")

    # write to html file

    with open(directory + "topicOutput.html", "w") as file:
        file.write(str(soup))

    options = {'enable-local-file-access': None}
    imgkit.from_file(directory + "topicOutput.html", directory + "topic.png", options=options)
    print("done")


def generateCommentScreenShot(comment : RedditComment, commentId):
    # get post directory
    directory = "./" + comment.obj.submission.id + "/"
    html = open("templates/comment.html")
    soup = BeautifulSoup(html, "html.parser")
    # replace username
    usernameTag = soup.find("p", {"class": "username"})
    usernameTag.string = comment.author.authorName

    # replace img
    profilePicTag = soup.new_tag("img", attrs={"class": "profile-pic", "src": comment.author.authorImage})
    sideBarTag = soup.find("div", {"class" : "side-bar"})
    sideBarTag.append(profilePicTag)

    verticalLineTag = soup.new_tag("div", attrs={"class": "vertical-line"})
    sideBarTag.append(verticalLineTag)

    # replace comment
    commentTag = soup.find("p", {"class": "comment-content-text"})
    commentTag.string = comment.comment

    # replace upvotes
    upvotesTag = soup.find("p", {"class": "comment-text"})
    upvotesTag.string = str(comment.upvotes)

    # replace timestamp
    timestampTag = soup.find("p", {"class": "posted-by"})
    timestampTag.string = str(formatTime(comment.timestamp)) + " hr. ago"

    # replace awards
    # get awards on comment

    for award in comment.obj.all_awardings:
        awardCount = award['count']
        awardIconeURL = award['icon_url']
        # add new block of code
        if len(comment.obj.all_awardings) == 1 and comment.obj.all_awardings[0] == award:
            awardTag = soup.new_tag("div", attrs={"class": "float-child", "style": "margin-right:20px;"})
        else:
            awardTag = soup.new_tag("div", attrs={"class": "float-child"})
        awardTag.append(soup.new_tag("img", attrs={"src": awardIconeURL, "class": "award-icon less-margin float-child"}))
        awardCountTag = soup.new_tag("p", attrs={"class": "award-count less-margin float-child"})
        awardCountTag.string = str(awardCount)
        awardTag.append(awardCountTag)
        awardsTag = soup.find("div", attrs={"class": "comment-header"})
        awardsTag.append(awardTag)

    # write to html file
    filename = "comment" + str(commentId) + ".png"
    filenameOutput = "comment" + str(commentId) + "output.html"
    with open(directory + filenameOutput, "w") as file:
        file.write(str(soup))

    options = {'enable-local-file-access': None}
    imgkit.from_file(directory + filenameOutput, directory + filename, options=options)


def getMP3AudioDuration(mp3File):
    # get duration of mp3 file
    audio = MP3(mp3File)
    duration = audio.info.length
    return duration


class FrameObject:
    def __init__(self, id, imageClip : mpy.ImageClip , imageFile, audioFile, duration):
        self.id = id
        self.imageClip = imageClip
        self.imageFile = imageFile
        self.audioFile = audioFile
        self.duration = duration


def createVideo(post : RedditObject):
    # get post directory
    directory = "./" + post.id + "/"

    videoFrames = []

    # get topic frame
    topicImage = directory + "topic.png"
    topicAudio = directory + "topic.mp3"
    topicDuration = getMP3AudioDuration(topicAudio)
    frame = mpy.ImageClip(topicImage, duration=topicDuration)
    frame = frame.set_audio(mpy.AudioFileClip(topicAudio))
    topicFrame = FrameObject(99, frame, topicImage, topicAudio, topicDuration)
    videoFrames.append(topicFrame)

    # get comment frames
    for i in range(len(post.comments)):
        commentImage = directory + "comment" + str(i) + ".png"
        commentAudio = directory + "comment" + str(i) + ".mp3"
        commentDuration = getMP3AudioDuration(commentAudio)
        frame = mpy.ImageClip(commentImage, duration=commentDuration)
        frame = frame.set_audio(mpy.AudioFileClip(commentAudio))
        commentFrame = FrameObject(i, frame, commentImage, commentAudio, commentDuration)
        videoFrames.append(commentFrame)


    video = mpy.concatenate_videoclips([x.imageClip for x in videoFrames], method="compose")
    video.write_videofile(directory + "video.mp4", fps=24)
    print("done")

def main():
    post = getPosts(2)[0]
    generateTopicScreenShot(post)
    for i in range(len(post.comments)):
        generateCommentScreenShot(post.comments[i], i)
    
    postToSpeech(post)
    createVideo(post)

    post2 = getPosts(2)[1]
    generateTopicScreenShot(post2)
    for i in range(len(post2.comments)):
        generateCommentScreenShot(post2.comments[i], i)
    
    postToSpeech(post2)
    createVideo(post2)

main()
