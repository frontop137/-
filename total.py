import requests
import json
import time
import cv2


classroomid = '4449749'
sign = '7GmGPsM8ci5'
term = 'latest'
universityid = '2627'
cookie = ""


headers1 = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.'
                         '0.4240.111 Safari/537.36',
           'cookie': '',
           'referer': 'https://scut.yuketang.cn/pro/lms/7GmGPsM8ci5/%s/studycontent' % classroomid,
           'university-id': universityid,
           'xtbz': 'cloud'
           }


def get_videoid(crid):
    """
    获取需要观看视频的编号
    :param crid: 教室id
    :return: 储存着需要观看视频编号的列表
    """
    chap_url = 'https://scut.yuketang.cn/mooc-api/v1/lms/learn/course/' \
               'chapter?cid=%s&sign=%s&term=%s&uv_id=%s' % (crid, sign, term, universityid)
    response = requests.get(chap_url, headers=headers1)
    response.encoding = response.apparent_encoding
    jsdata = json.loads(response.text)
    cid = jsdata['data']['course_id']
    course_chapters = jsdata['data']['course_chapter']
    vid = []
    for chap in course_chapters:
        for sec in chap['section_leaf_list']:
            if sec['name'] != '章节测试题':
                vid.append(sec['id'])
    return list(map(lambda x: str(x), vid)), cid


def get_videourl(vid):
    """
    获取视频url函数
    :param vid: 视频id列表
    :return: 视频url列表
    """
    url_head = 'https://scut.yuketang.cn/pro/lms/%s/%s/video/' % (sign, classroomid)
    vurl = list(map(lambda x: url_head+x, vid))
    return vurl


def get_userinfo():
    user_url = 'https://scut.yuketang.cn/edu_admin/get_user_basic_info/?term=latest&uv_id=%s' % universityid
    response = requests.get(user_url, headers=headers1)
    print('用户姓名：', json.loads(response.text)['data']['user_info']['name'])
    userid = json.loads(response.text)['data']['user_info']['user_id']
    return userid


userid = get_userinfo()
courseid = get_videoid(classroomid)[1]
video_id = get_videoid(classroomid)[0]
video_url = get_videourl(video_id)

for id in video_id:
    print('正在观看视频id：', id)
    headers2 = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
               'cookie': '',
               'origin': 'https://scut.yuketang.cn',
               'referer': video_url[video_id.index(id)],
               'xtbz': 'cloud',
               'content-type': 'application/json'
                }

    # 获取视频时长
    def get_videolen(vid):
        ask_video_url = 'https://scut.yuketang.cn/api/open/audiovideo/' \
                        'playurl?_date=%s&term=latest&video_id=%s&' \
                        'provider=cc&file_type=1&is_single=0' % (str(int(time.time() * 1000)), get_videoinfo(vid)[1])
        origin_url = requests.get(ask_video_url, headers=headers2)
        origin_url.encoding = origin_url.apparent_encoding
        try:
            origin_url = json.loads(origin_url.text)['data']['playurl']['sources']['quality10'][0]
        except:
            origin_url = json.loads(origin_url.text)['data']['playurl']['sources']['quality20'][0]
        # 计算时长
        cap = cv2.VideoCapture(origin_url)
        if cap.isOpened():
            fps = cap.get(5)
            framenum = cap.get(7)
            duration = int(framenum / fps)
            return duration
        else:
            return 0

    # 获取视频信息
    def get_videoinfo(vid):
        """
        获取视频信息函数
        :param vid: 视频id
        :return: 第一个参数为sku_id（type->int）,第二个参数为cc(type->str)
        """
        info_url = 'https://scut.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/' \
                   '%s/%s/?sign=7GmGPsM8ci5&term=latest&uv_id=%s' % (classroomid, vid, universityid)
        info = requests.get(info_url, headers=headers2)
        info.encoding = info.apparent_encoding
        info = json.loads(info.text)['data']
        return info['sku_id'], info['content_info']['media']['ccid']

    # 心跳包post请求网址
    heartbeat_url = 'https://scut.yuketang.cn/video-log/heartbeat/'

    length = get_videolen(id)
    sku_id = get_videoinfo(id)[0]
    cc = get_videoinfo(id)[1]

    hb_list = []
    # 心跳包模板
    template = {
        'i': 5,
        'et': '',
        'p': 'web',
        'n': 'cc',
        'lob': 'cloud4',
        'cp': 0,  # 观看进度
        'fp': 0,
        'tp': 0,
        'sp': 1,
        'ts': int(time.time() * 1000),
        'u': userid,  # 用户id
        'uip': '',
        'c': courseid,   # 课程id
        'v': id,       # 视频id
        'skuid': sku_id,   # skuid
        'classroomid': classroomid,   # 教室id
        'cc': cc,
        'd': length,          # 视频时长
        'pg': id + '_12bvp',
        'sq': 0,   # 心跳包序列
        't': 'video'
    }

    # 先发送一次空包
    requests.post(heartbeat_url, headers=headers2, data=json.dumps({"heart_data": []}))

    # loadstart
    ls = template.copy()
    ls['et'] = 'loadstart'
    ls['d'] = 0
    ls['sq'] = 1
    hb_list.append(ls)

    # seeking
    sk = template.copy()
    sk['et'] = 'seeking'
    sk['sq'] = 2
    hb_list.append(sk)

    # loadeddata
    ld = template.copy()
    ld['et'] = 'loadeddata'
    ld['sq'] = 3
    hb_list.append(ld)

    # play
    play = template.copy()
    play['et'] = 'play'
    play['sq'] = 4
    hb_list.append(play)

    # playing
    playing = template.copy()
    playing['et'] = 'playing'
    playing['sq'] = 5
    hb_list.append(playing)

    sq = 6
    # heartbeat
    for i in range(0, length, 5):
        hb = template.copy()
        hb['et'] = 'heartbeat'
        hb['cp'] = i
        hb['sq'] = sq
        hb_list.append(hb)
        sq += 1
        if len(hb_list) == 10:
            hb_data = {'heart_data': hb_list}
            send = requests.post(heartbeat_url, headers=headers2, data=json.dumps(hb_data))
            # print(send.status_code)
            try:
                rate = requests.get('https://scut.yuketang.cn/'
                                    'video-log/get_video_watch'
                                    '_progress/?cid=%s&'
                                    'user_id=%s&classroom_id=%s&'
                                    'video_type=video&vtype=rate&'
                                    'video_id=%s&snapshot=1&term=latest&uv_id=%s'
                                    % (str(courseid), str(userid), classroomid, id, universityid), headers=headers2)
                rate = json.loads(rate.text)
                print('观看进度：', rate[id]['rate'])
            # print(hb_list)
            except:
                pass
            hb_list.clear()
            time.sleep(1)

    # 再发最后一个heartbeat
    hb = template.copy()
    sq += 1
    hb['et'] = 'heartbeat'
    hb['cp'] = length
    hb['sq'] = sq
    hb_list.append(hb)

    # pause
    pause = template.copy()
    sq += 1
    pause['et'] = 'pause'
    pause['cp'] = length
    pause['sq'] = sq
    hb_list.append(pause)

    # videoend
    ve = template.copy()
    sq += 1
    ve['et'] = 'videoend'
    ve['cp'] = length
    ve['sq'] = sq
    hb_list.append(ve)

    requests.post(heartbeat_url, headers=headers2, data=json.dumps({'heart_data': hb_list}))

    rate = requests.get('https://scut.yuketang.cn/video-log/get_video_watch_progress'
                        '/?cid=%s&user_id=%s&classroom_id=%s&video_typ'
                        'e=video&vtype=rate&video_id=%s&snapshot=1&term=latest&uv_id=%s'
                        % (str(courseid), str(userid), classroomid, id, universityid),
                        headers=headers2)
    rate.encoding = rate.apparent_encoding
    print('是否完成观看：', json.loads(rate.text)[id]['completed'])


