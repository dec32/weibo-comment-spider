import random
import time
import requests
import re
import yaml

with open("run_conf.yml") as f:
    '''
    desc:
        读取用户定义的参数
    params:
        cookie:     利用浏览器的调试工具获得，用于模拟登录
        weibo_id:   希望爬取评论的微博对应的移动端 id
        sleep_time: 平均每次查询之间间隔多少秒（会根据此值随机生成休眠时间，使平均值为此值）
    '''
    conf = yaml.full_load(f)
    cookie = conf['cookie']
    weibo_id = conf['weibo_id']
    sleep_time = conf['sleep_time']


# 以下是程序的主体部分

# 固定的 headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Cookie': cookie,
}

# 统计爬取的总评论数
num_comments = 0
# 接口的分页参数
max_id = 0
max_id_type = 0
# 获取 session，保证所有请求使用同一个 session，否则会被微博识别为登录无效，并被重定向到登陆页面
session = requests.session()
base_url = "https://m.weibo.cn/comments/hotflow?id={}&mid={}".format(weibo_id, weibo_id)
# 用于保存结果的 txt
result_file = open("result.txt", "w+", encoding="utf-8")

while True:
    url = base_url + "&max_id_type={}&max_id={}".format(max_id_type, max_id)
    # 获取 res 中的 json 数据
    weibo_data = session.get(url=url, headers=headers)
    json_str = weibo_data.json()
    # json 为 {"ok": 0} 时表示服务器拒绝返回更多数据（可能是已经爬取完所有评论，也有可能是触发了反爬机制）
    if json_str['ok'] == 0:
        # print("ok = 0")
        break

    # 获取评论列表和下一组评论的分页参数
    comments_list = json_str['data']['data']
    # 循环输出评论
    count = 0
    for comment_item in comments_list:
        comment = comment_item['text']
        # 清洗掉一些没意义的东西
        label_filter = re.compile(r'(<span.*>.*</span>)*(<a.*>.*</a>)?')
        clean_comment = re.sub(label_filter, '', comment)
        if clean_comment != "":
            result_file.writelines(clean_comment + '\n')
            count += 1
    num_comments += count
    print("本次爬取: " + str(count) + "\t总计爬取: " + str(num_comments) + "\t(" + str(url) + ")")

    # 输出本轮的评论以后判断下一轮 max_id 的值，为 0 则说明已没有下一轮数据可取，终止程序
    max_id = json_str['data']['max_id']
    max_id_type = json_str['data']['max_id_type']
    if max_id == 0:
        # print("max_id = 0")
        break
    # 防止触发反爬机制
    time.sleep(random.randint(1, sleep_time * 2 - 1))

result_file.close()
