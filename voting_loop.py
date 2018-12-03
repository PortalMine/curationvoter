import logging
import configparser
import time
import json
from json import JSONDecodeError
from pprint import pprint

from beem.account import Account
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.steem import Steem


config = configparser.ConfigParser()
config.read('config.ini')

log = logging.getLogger(__name__)
log.setLevel(level='INFO')

s = Steem(keys=config['GENERAL']['posting_key'], node='https://api.steemit.com', nobroadcast=config.getboolean('GENERAL', 'testing'), bundle=True)
a = Account(account=config['GENERAL']['acc_name'], steem_instance=s)
b = Blockchain(steem_instance=s)


def vote(author, perm):  # vote the post
    success = False

    with open(file="text_files/" + config['VOTER']['comment_file'], mode='rb') as file:  # loading comment text
        comment_body = file.read().decode('UTF-8')
    print('Loaded comment text.')

    permlink = author + '/' + perm
    c = Comment(authorperm=permlink, steem_instance=s)
    try:
        tags = c.json_metadata['tags']
        for check in config['VOTER']['banned_tags'].replace(' ', '').split(','):  # scanning for banned tags
            if check in tags:
                print('\n    Dumped because of banned tags.\n')
                break
        else:
            penalty = c.get_curation_penalty()
            if config['GENERAL']['acc_name'] not in c.get_votes():  # check if bot has already voted
                if penalty > 0.0:
                    print('    FOUND post: ' + permlink)
                    wait = penalty*config.getint('VOTER', 'vote_after_minutes')*60
                    print('    WAITING ' + str(wait) + ' seconds')
                    time.sleep(wait)

                    try:
                        c.upvote(weight=config.getfloat('VOTER', 'vote_weight'), voter=config['GENERAL']['acc_name'])  # Finally vote post and leave a comment
                        c.reply(body=comment_body, author=config['GENERAL']['acc_name'])
                        pprint(s.broadcast())
                        print('      VOTED ' + permlink)
                        success = True
                    except Exception as e:
                        log.warning('ERROR: ' + str(e))
                        log.warning('      Didn\'t vote ' + permlink)

                else:
                    print('      Post is edit after 30 minutes')
            else:
                print('      Post already voted.')
    except KeyError as e:
        log.warning('\n    No tags on this post. (2)\n      ' + str(e))

    return success


def scan():
    counter = 0
    for post in b.stream(opNames=['comment']):  # scan for posts
        try:
            if post['parent_author'] == '':
                counter += 1
                print('\r' + str(counter), end=' scanned posts.', flush=True)
                tags = json.loads(post['json_metadata'])['tags']

                for check in config['VOTER']['voted_tags'].replace(' ', '').split(','):  # scanning for wanted tags in posts
                    if check in tags:
                        print('\n  In block ' + str(post['block_num']))
                        if vote(post['author'], post['permlink']):  # Vote if selected tags are used
                            break
                        counter = 0
                else:
                    continue
                break

        except JSONDecodeError as e:  # catching exceptions
            log.warning('\n  JSON Failure :\n    ' + str(e))
        except KeyError as e:
            log.warning('\n  No tags on post. (1)\n    ' + str(e))
        except Exception as e:
            log.warning('\n  A really strange error occured...\n    ' + str(e))


def wait_for_vp():  # wait for enough voting power, then search for posts
    while True:
        a.refresh()
        vp = a.get_voting_power()
        print(a.name+' has '+str(vp))
        if vp > config.getint('VOTER', 'min_vp'):
            print('VP is over ' + config['VOTER']['min_vp'] + '%\n')
            try:
                scan()
            except Exception as e:
                log.warning('Scan failed. Error:\n' + str(e))
        else:
            time.sleep(config.getint('VOTER', 'check_vp_interval'))
        config.read('config.ini')


if __name__ == '__main__':
    wait_for_vp()
