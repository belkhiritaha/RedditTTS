from datetime import datetime
from gtts import gTTS
import praw
from bs4 import BeautifulSoup
import imgkit
from datetime import datetime
import os
import moviepy.editor as mpy
from mutagen.mp3 import MP3
import random
from PIL import Image
import soundfile as sf
from pysndfx import AudioEffectsChain
from pydub import AudioSegment
import pyrubberband as pyrb
import wave

# create class RedditAuthor
class RedditAuthor:
    def __init__(self, authorName : str, authorImage : str):
        self.authorName = authorName
        self.authorImage = authorImage


# create class RedditObject
class RedditObject:
    def __init__(self, topic : str, comments : list, id : str, upvotes : int, author, timestamp, nbComments, awards, isNSFW, obj, sentences):
        self.id = id
        self.topic = topic
        self.comments = comments
        self.upvotes = upvotes
        self.author = author
        self.timestamp = timestamp
        self.nbComments = nbComments
        self.awards = awards
        self.isNSFW = isNSFW
        self.obj = obj
        self.sentences = sentences

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


def commentHasLink(comment):
    if comment.find("http") != -1:
        return True
    else:
        return False


def getPosts(subreddit ,numberOfPosts):
    postsList = []         
    redditUsername, redditPassword = readCredentials()
    reddit = praw.Reddit(client_id='HSpPGBBIzLbXoGHSUvaMnQ',
                         client_secret='nymnF7nwF8Vd8UUOARfzyE73m8etoQ',
                         user_agent='reditTTS (by /u/DenseInspection1507)',
                         username=redditUsername,
                         password=redditPassword)
    print("Connected to Reddit")
    subreddit = reddit.subreddit(subreddit)
    print("Querrying subreddit:", subreddit.display_name)
    # get all time best posts
    for submission in subreddit.hot(limit=numberOfPosts):
        print("Exploring submission")
        commentList = []
        for top_level_comment in submission.comments.list()[:10]:
            print("Exploring comment")
            if type(top_level_comment) is praw.models.Comment and len(top_level_comment.body) > 15 and commentHasLink(top_level_comment.body) != True:
                try:
                    print(top_level_comment.author.name)
                    author = RedditAuthor(top_level_comment.author.name, top_level_comment.author.icon_img)
                except AttributeError or TypeError:
                    author = RedditAuthor("[deleted]", "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png")
                comment = RedditComment(top_level_comment.body, author, top_level_comment.ups, top_level_comment.created_utc, top_level_comment)
                commentList.append(comment)
        
        sentences = []
        if submission.selftext != "":
            currentText = submission.selftext
            # split into sentences
            sentences = currentText.split(".")

            # join 2 sentences
            for i in range(len(sentences)):
                if i < len(sentences) - 1:
                    sentences[i] = sentences[i] + "." + sentences[i+1]
                    sentences.pop(i+1)
        
        # remove sentences that are ""
        for i in range(len(sentences)):
            if sentences[i] == "":
                sentences.pop(i)

        post = RedditObject(submission.title, commentList, submission.id, submission.ups, submission.author.name, submission.created_utc, submission.num_comments, submission.all_awardings, submission.over_18, submission, sentences)
        postsList.append(post)
        print("added post")
    return postsList


def postToSpeech(post):
    print("Generating topic audio")
    directory = "./" + post.id + "/"
    topic = gTTS(post.topic, lang="en-us", slow=False, tld="co.uk")
    topic.save(directory +"topic.mp3")
    sound = AudioSegment.from_mp3(directory + "topic.mp3")
    sound.export(directory + "topic.wav", format="wav")
    # speed up topic audio by 1.5x
    s,rate = sf.read(directory + "topic.wav")
    stretch = pyrb.time_stretch(s, rate, 1.2)
    pitch = pyrb.pitch_shift(stretch, rate, 0.5)
    sf.write(directory + "topic.wav", stretch, rate, format="wav")


    if post.obj.selftext != "":
        sentences = post.sentences
        for sentence in sentences:
            submissionBody = gTTS(sentence, lang="en-us", slow=False, tld="co.uk")
            submissionBody.save(directory + "body" + str(sentences.index(sentence)) + ".mp3")
            sound = AudioSegment.from_mp3(directory + "body" + str(sentences.index(sentence)) + ".mp3")
            sound.export(directory + "body" + str(sentences.index(sentence)) + ".wav", format="wav")
            # speed up body audio by 1.5x
            s,rate = sf.read(directory + "body" + str(sentences.index(sentence)) + ".wav")
            stretch = pyrb.time_stretch(s, rate, 1.2)
            pitch = pyrb.pitch_shift(stretch, rate, 0.5)
            sf.write(directory + "body" + str(sentences.index(sentence)) + ".wav", stretch, rate, format="wav")

    num = 0
    for comment in post.comments:
        print("Generating comment audio")
        speech = gTTS(comment.comment, lang="en", slow=False)
        speech.save(directory + "comment" + str(num) + ".mp3")
        sound = AudioSegment.from_mp3(directory + "comment" + str(num) + ".mp3")
        sound.export(directory + "comment" + str(num) + ".wav", format="wav")
        # speed up comment audio by 1.5x
        s,rate = sf.read(directory + "comment" + str(num) + ".wav")
        stretch = pyrb.time_stretch(s, rate, 1.2)
        pitch = pyrb.pitch_shift(stretch, rate, 0.5)
        sf.write(directory + "comment" + str(num) + ".wav", pitch, rate, format="wav")
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
    for award in post.awards[:5]:
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

    # if post is nsfw
    if post.isNSFW:
        topicContentTag = soup.find("div", attrs={"class": "topic-content"})
        nsfwTag = soup.new_tag("p", attrs={"class": "nsfw float-child"})
        nsfwTag.string = "nsfw"
        topicContentTag.append(nsfwTag)


    # write to html file
    with open(directory + "topicOutput.html", "w") as file:
        file.write(str(soup))

    options = {'enable-local-file-access': None}
    imgkit.from_file(directory + "topicOutput.html", directory + "topic.png", options=options)

    # crop image
    img = Image.open(directory + "topic.png")
    w, h = img.size
    img = img.crop((0, 0, w/2, h))
    img.save(directory + "topic.png")

    print("done")


def generateSubmissionBodyScreenShot(post : RedditObject):
    # get post directory
    directory = "./" + post.id + "/"
    html = open("templates/body.html")
    soup = BeautifulSoup(html, "html.parser")

    sentences = post.sentences

    for sentence in sentences:
        # replace body
        bodyTag = soup.find("p", {"class": "comment-content-text"})
        bodyTag.string = sentence

        # write to html file
        with open(directory + "bodyOutput.html", "w") as file:
            file.write(str(soup))

        sentenceIndex = sentences.index(sentence)
        filename = directory + "body" + str(sentenceIndex) + ".png"

        options = {'enable-local-file-access': None}
        imgkit.from_file(directory + "bodyOutput.html", filename, options=options)

        # remove bodyOutput.html
        os.remove(directory + "bodyOutput.html")

        # crop image
        img = Image.open(filename)
        w, h = img.size
        img = img.crop((0, 0, w/2, h))
        img.save(filename)


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

    for award in comment.obj.all_awardings[:5]:
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

    # crop image
    img = Image.open(directory + filename)
    w, h = img.size
    img = img.crop((0, 0, w * (50/100), h))
    img.save(directory + filename)


def getWAVAudioDuration(wavFile):
    # get duration of wav file
    audio = wave.open(wavFile, 'r')
    duration = audio.getnframes() / audio.getframerate()
    return duration


class FrameObject:
    def __init__(self, id, imageClip : mpy.ImageClip , imageFile, audioFile, duration):
        self.id = id
        self.imageClip = imageClip
        self.imageFile = imageFile
        self.audioFile = audioFile
        self.duration = duration


def createVideo(post):
    print("Creating video")
    # get post directory
    directory = "./" + post.id + "/"

    videoLength = 0
    videoFrames = []

    # get topic frame
    topicImage = directory + "topic.png"
    topicAudio = directory + "topic.wav"
    topicDuration = getWAVAudioDuration(topicAudio)

    frame = mpy.ImageClip(topicImage, duration=topicDuration + 0.5)
    frame = frame.set_audio(mpy.AudioFileClip(topicAudio))
    topicFrame = FrameObject(99, frame, topicImage, topicAudio, topicDuration)
    videoFrames.append(topicFrame)

    videoLength += topicDuration

    if post.obj.selftext != "":
        for sentence in post.sentences:    
            bodyImage = directory + "body" + str(post.sentences.index(sentence)) + ".png"
            bodyAudio = directory + "body" + str(post.sentences.index(sentence)) + ".wav"
            bodyDuration = getWAVAudioDuration(bodyAudio)
            frame = mpy.ImageClip(bodyImage, duration=bodyDuration + 0.5)
            frame = frame.set_audio(mpy.AudioFileClip(bodyAudio))
            bodyFrame = FrameObject(100, frame, bodyImage, bodyAudio, bodyDuration)
            videoFrames.append(bodyFrame)

            videoLength += bodyDuration
    
    # get comment frames
    i = 0
    while i < (len(post.comments)):
        commentImage = directory + "comment" + str(i) + ".png"
        commentAudio = directory + "comment" + str(i) + ".wav"
        commentDuration = getWAVAudioDuration(commentAudio)
        print("comment duration: " + str(commentDuration))
        print("video length: " + str(videoLength))
        if videoLength + commentDuration < 120 or i == 0:        
            frame = mpy.ImageClip(commentImage, duration=commentDuration + 0.5)
            frame = frame.set_audio(mpy.AudioFileClip(commentAudio))
            commentFrame = FrameObject(i, frame, commentImage, commentAudio, commentDuration)
            videoFrames.append(commentFrame)
            videoLength += commentDuration
        i += 1
    video = mpy.concatenate_videoclips([x.imageClip for x in videoFrames], method="compose")

    rawBackground = mpy.VideoFileClip("../Downloads/backgroundVideo.mp4")
    rawBackground = rawBackground.set_audio(None)
    rawBackgroundDuration = rawBackground.duration

    # get random subclip
    randomStart = random.randint(30, int(rawBackgroundDuration) - int(video.duration) - 30)
    backgroundVideo = rawBackground.subclip(randomStart, int(video.duration) + randomStart + 0.5)
    backgroundVideo = backgroundVideo.resize((1080, 1920))

    # set new video dimensions
    videoWidth = video.w
    videoHeight = video.h
    video = video.resize((videoWidth * 1.8 , videoHeight * 1.8))

    # center video
    video = video.set_position("center")

    # put video on top of background video
    video = mpy.CompositeVideoClip([backgroundVideo, video])

    video.write_videofile(directory + "video.mp4", fps=60)


def main():
    posts = getPosts("amitheasshole" , 2)
    for post in posts[1:]:
        generateTopicScreenShot(post)
        if post.obj.selftext != "":
            generateSubmissionBodyScreenShot(post)
        for i in range(len(post.comments)):
            generateCommentScreenShot(post.comments[i], i)
        
        postToSpeech(post)
        createVideo(post)
    
main()
