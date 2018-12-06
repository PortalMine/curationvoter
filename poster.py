from pprint import pprint
import logging
import datetime
import configparser
from datetime import datetime
from beem.steem import Steem
from beem.comment import Comment
from beem.account import Account

config = configparser.ConfigParser()
config.read('config.ini')

log = logging.getLogger(__name__)

s = Steem(keys=config['GENERAL']['posting_key'], node='https://api.steemit.com', nobroadcast=config.getboolean('GENERAL', 'testing'))
a = Account(account=config['GENERAL']['acc_name'])


def make_table():  # loading table of voted posts
    table_string = '\n| User/in | Beitragslink (Steemit.com) | Bild (Busy.org) | Gewicht |\n' \
                   '|---------|--------------| ---- | --- |\n'

    all_votes = a.get_account_votes()

    latest_vote = config['POSTER']['last_post_vote']

    for vote in all_votes:  # creating table
        if vote['time'] > config['POSTER']['last_post_vote']:

            if vote['time'] > latest_vote:
                latest_vote = vote['time']

            c = Comment(authorperm=vote['authorperm'])
            link_steemit = '[' + c.title.replace('|', '-').replace('[', '(').replace(']', ')') + '](https://steemit.com/' + c.authorperm + ')'
            image = '[![Kein Bild]([PICTURE])](https://busy.org/' + c.authorperm+')'
            try:
                image = image.replace('[PICTURE]', 'https://steemitimages.com/500x0/'+c.json_metadata['image'][0])
            except KeyError as e:
                log.warning(str(e))
            except IndexError as e:
                log.warning(str(e))
            table_string += '| @'+c.author+'|'+link_steemit+'|'+image+'|'+str(vote['percent']/100)+'|\n'
    with open(file='config.ini', mode='w+') as file:
        config['POSTER']['last_post_vote'] = latest_vote
        config.write(file)
    return table_string


def make_post_body(date):
    with open(file=config['POSTER']['supporters_file']) as file:  # loading supporters
        supporters = file.read()
    with open(file=config['POSTER']['delegators_file']) as file:  # loading delegators
        delegators = file.read()
    with open(file=config['POSTER']['body_file'], mode='rb') as file:  # loading post text and replacing placeholders
        post_body = file.read().decode('UTF-8').\
            replace('[DATE]', date).\
            replace('[TABLE_POSTS]', make_table()).\
            replace('[SUPPORTERS]', supporters).\
            replace('[DELEGATORS]', delegators)
    return post_body


def post():
    t = datetime.now()
    date = str("{0:02}".format(t.day) + '.' +
               "{0:02}".format(t.month) + '.' +
               "{0:02}".format(t.year))
    title = config['POSTER']['title'].replace('[DATE]', date)
    print(title)
    body = make_post_body(date)
    print(body)
    pprint(s.post(title=title, body=body, author=config['GENERAL']['acc_name'], tags=config['POSTER']['tags'].replace(' ', '').split(','),
                  self_vote=config.getboolean('POSTER', 'self_vote'), app="@curationvoter by @portalmine for @backinblackdevil"))


if __name__ == '__main__':
    post()
