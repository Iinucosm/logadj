from compileall import compile_dir
from distutils.errors import LinkError
from operator import eq, length_hint
from pickle import NONE
import sys
from xmlrpc.client import boolean
from chardet import detect
import shutil
import re
import os


#編集用のバックアップファイル作成
def filecopy(file, code):
    with open(file, encoding=code, errors='ignore') as fl:
        bk_data = fl.read()
    with open(file + ".bk", mode='w', encoding=code, errors='ignore') as f:
        f.write(bk_data)

#指定文字を含む行とその上の行を削除
def del_word(file, word, code, num):
    n = num
    filecopy(file, code)
    with open(file, mode="w", encoding=code,) as f:
        f.write("")
    for line in open(file + ".bk", encoding=code):
        if word[n * -1] in line:
            n += 1
            continue
        with open(file, mode="a", encoding=code) as f:
            f.write(line)
    os.remove(file + ".bk")

# 特定行の削除
def delete_len(file, code, num):
    with open(file, mode="r", encoding=code) as f:
        del_word(file, f.readlines(), code, num)

# ホスト名を切り離す
def set_config(line):
    config = ""
    if line.find('#') == -1: config = line.partition(">")[0]; config = config + ">"
    else: config = line.partition('#')[0]; config = config + "#"
    return config

# 入力されたコマンドを切り離す
def set_command(line):
    command = ""
    if line.find('#') == -1: command = line.partition(">")[2]
    else: command = line.partition('#')[2]
    return command

# showがあるかどうかを確認
def flag_show(line):
    if re.search('(#|>).*?(s.*?h.*?o.*?w.*?|sh)', line) is not None:
        return True
    return False

# yamahaのconfigコマンドを探知
def flag_yamaha_config(line):
    cmd = set_command(line)
    if "-" in cmd:
        return False
    if re.search('c.*?o.*?n.*?f.*?', cmd) is not None:
        return True
    return False

# yamahaのlog reverseコマンドを探知
def flag_yamaha_log(line):
    cmd = set_command(line)
    if re.search("l.*?o.*?g.*?r.*?e.*?v.*?e.*?r.*?", cmd) is not None:
        return True
    return False

# catalystのrunningコマンドを探知
def flag_cisco_running(line):
    cmd = set_command(line)
    if re.search("r.*?u.*?n.*?n.*?|run", cmd) is not None:
        return True
    return False

# catalystのstartupコマンドを探知
def flag_cisco_startup(line):
    cmd = set_command(line)
    if re.search("s.*?t.*?a.*?r.*?t.*?|star", cmd) is not None:
        return True
    return False

# catalystのloggingコマンドを探知
def flag_cisco_log(line):
    cmd = set_command(line)
    if re.search("l.*?o.*?g.*?g.*?i.*?", cmd) is not None:
        return True
    return False

#--------------2023/3/30新規追加-----------------------

# pingコマンドを探知
def flag_ping(line):
    cmd = set_command(line)
    if re.search("p.*?i.*?n.*?g.*?((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]).*?", cmd) is not None:
        return True
    return False

#------------------------------------------------------

#　フラグが立ったコマンドが正しいかを確認
def judge_line(line, num):
    if num == 1:
        if re.search('^#',line) is not None:
            return True
    if num == 2:
        if re.search(r'^[1-2][0-9]{3}/[0-2][0-9]/[0-3][0-9]',line) is not None:
            return True
    if num == 3:
        if re.search(r'Building',line) is not None:
            return True
    if num == 4:    
        if re.search(r'^Using',line) is not None:
            if re.search(r'sing',line) is not None:
                if "bytes" in line:
                    return True
    if num == 5:
        if re.search('logging', line) is not None:
            return True
    if num == 6:
        ptint("aa")
        #Ciscoのping
        if re.search(r'Type escape sequence to abort"' ) is not None:
            return True
        #Yamahaのping
        if re.search(r'^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])', line) is not None:
            return True
        #Yamahaのpingミスを判定
        if line is False:
            return True
    
    return False


#　コマンドを確認する
def flagconfirm(line, allflag):
    if flag_show(line) is False:
        return 0
    if flag_yamaha_config(line) is True:
        allflag[1] = True
    if flag_yamaha_log(line) is True:
        allflag[2] = True
    if flag_cisco_running(line) is True:
        allflag[3] = True
    if flag_cisco_startup(line) is True:
        allflag[4] = True
    if flag_cisco_log(line) is True:
        allflag[5] = True
    for i in range(len(allflag)):
        if allflag[i] is True:
            return i
    return 0

# フラグが立った原因を削除し再確認
def reconfirm(prev_line, num, allflag):
    l = prev_line
    if num == 1:
        l = prev_line.replace("c","").replace("o", "").replace("n", "").replace("f", "")
    if num == 2:
        l = prev_line.replace("r","").replace("e", "").replace("v", "").replace("e", "").replace("r", "").replace("s", "").replace("e", "")
    if num == 3:
        l = prev_line.replace("r","").replace("u", "").replace("n", "")
    if num == 4:
        l = prev_line.replace("s","").replace("t", "").replace("a", "").replace("r", "")
    if num == 5:
        l = prev_line.replace("l","").replace("o", "").replace("g", "").replace("g", "")
    return flagconfirm(l, allflag)

def set_filename(file_name):
    if "/" in file_name:
        target = '/'
        idx = file_name.rfind(target)
        return file_name[idx+1:]
    return file_name


def main(path):
    filename=path
    osfilename = set_filename(filename)
    file_place= os.getcwd() + "/" + osfilename + "_log/"
    os.makedirs(file_place, exist_ok=True)
    ad_filename = file_place + "ad_" + osfilename
    ex_filename = file_place + "ex_" + osfilename

    #開くファイルの文字コードを自動検出
    try:
        with open(filename, "rb") as fl:
            binary = fl.read()
            character_code = detect(binary)
            with open(filename, mode='r', encoding=character_code['encoding'], errors='ignore') as f:
                data_lines = f.read()

        #ファイルから削除したい文字列を削除
        data_lines = data_lines.replace("---つづく---            ","")  #Yamaha
        data_lines = re.sub("---.*--            ","",data_lines)  #Yamaha
        data_lines = data_lines.replace(" --More--         ","")        #Cisco
        data_lines = re.sub("--More--  \(<space> = next page, <CR> = one line, C = continuous, Q = quit\).","",data_lines)                  #Allide
        data_lines = data_lines.replace("--More--","")                  #Allide2


        with open(ad_filename, mode="w", encoding=character_code['encoding']) as f:
            f.write(data_lines)
    except Exception:
        return 1
    m = 0

    #?行(YAMAHAでのTabキー押下)削除+エラー行とそのコマンドを削除
    for line in open(ad_filename, encoding=character_code['encoding']):
        e = re.search(r'^\?|\?\r|\?\n|\?\r\n', line)
        error_yamaha = "エラー:"
        error_cisco1 = "% Incomplete command."
        error_cisco2 = "% Unknown command"
        error_cisco3 = "% Invalid input detected at"
        #print(e), print(line)
        try:
            if m > 0:
                m-=1
                continue
            if error_yamaha in line:
                delete_len(ex_filename, character_code['encoding'], 1)
                continue
            if e is not None:
                continue
            if error_cisco2 in line:
                delete_len(ex_filename, character_code['encoding'], 2)
                continue
            if error_cisco1 in line:
                delete_len(ex_filename, character_code['encoding'], 1)
                m = 1
                continue
            if error_cisco3 in line:
                delete_len(ex_filename, character_code['encoding'], 2)
                m = 1
                continue
            
            with open(ex_filename, mode="a", encoding=character_code['encoding']) as f:
                f.write(line)
        except PermissionError:
            return 2

#config抽出

    state = 0
    times = [1] * 6
    configname_list = ["Other_", "_config_", "_log_", "_running_", "_startup_", "_logging_", "_pingtest_"]
    config_name = ""
    allflag = [False] * 7
    prev_line = ""

    flag = False
    try:
        for line in open(ex_filename, encoding=character_code['encoding']):
            if "enable" in set_command(line):
                config_name = set_config(line)
            if "administrator" in set_command(line):
                config_name = set_config(line)
            if flag_show(line) is True:
                #print("show"); print(flag_show(line))
                config_name = set_config(line)
                #print(flag_cisco_startup(line))
                #print("")
                if state == 0:
                    if flag_yamaha_config(line) is True:
                        allflag[1] = True
                        state = 1
                        prev_line = line
                        continue
                    if flag_yamaha_log(line) is True:
                        allflag[2] = True
                        state = 2
                        prev_line = line
                        continue
                    if flag_cisco_running(line) is True:
                        allflag[3] = True
                        state = 3
                        prev_line = line
                        continue
                    if flag_cisco_startup(line) is True:
                        allflag[4] = True
                        state = 4
                        prev_line = line
                        continue
                    if flag_cisco_log(line) is True:
                        allflag[5] = True
                        state = 5
                        prev_line = line
                        continue
            if flag_ping(line) is True:
                config_name = set_config(line)
                state = 6
                allflag[6] = True
                prev_line = line
                continue
            #フラグが建った次の行の場合、コマンドが正しいか確認
            if state != 0:
                for i in range(len(allflag)):
                    if allflag[i] is True:
                        allflag[i] = False
                        #次の行にホスト名が出現したらTabキー押下とみなしその行を判定
                        if config_name in line:
                            state = reconfirm(line, 0, allflag)
                            continue
                        #ホスト名が出現しなかった場合、コマンドが正しいか判定
                        if judge_line(line,i) is False:
                            state = reconfirm(prev_line, state, allflag)
                            flag = True
            
            #フラグが立った状態で、「ホスト名#」または「ホスト名>」を探知した場合、その行にてコマンドが入力されているかどうか確認
            #それ以外の場合は指定のファイルに追記
            if (state != 0) & (state!=6):         
                if config_name in line:
                    times[state] += 1
                    if config_name in prev_line:
                        times[state] -= 1
                    #print(times[state])
                    state = 0
                    conf = re.sub('\(.*\)','',config_name)
                    conf = re.sub('pp[0-9]*','',conf)
                    conf = re.sub('tunnel[0-9]*','',conf)
                    conf = conf.replace("#","")
                    conf = conf.replace(">","")
                    if flag is False:
                        state = reconfirm(line, 0, allflag)  
                    with open(file_place + conf + "_" + configname_list[0] + ".txt", mode="a", encoding=character_code['encoding']) as f:
                        f.write(line)
                    prev_line = line
                    continue
                else:
                    conf = re.sub('\(.*\)','',config_name)
                    conf = re.sub('pp[0-9]*','',conf)
                    conf = re.sub('tunnel[0-9]*','',conf)
                    conf = conf.replace("#","")
                    conf = conf.replace(">","")
                    with open(file_place + conf + configname_list[state] + str(times[state])  + ".txt", mode="a", encoding=character_code['encoding']) as f:
                        f.write(line)
                    prev_line = line
                    continue
            elif state == 6:
                state = 0
                if config_name == "":
                    with open(file_place + configname_list[state] + osfilename, mode="a", encoding=character_code['encoding']) as f:
                        f.write(line)
                        continue
                with open(file_place + conf + "_" + configname_list[state] + ".txt", mode="a", encoding=character_code['encoding']) as f:
                    if flag is True:
                        f.write(prev_line)
                        flag = False
                    f.write(line)
            # stateフラグが立っていない時はOtherファイルへ追記
            else:
                if config_name == "":
                    with open(file_place + configname_list[state] + osfilename, mode="a", encoding=character_code['encoding']) as f:
                        f.write(line)
                        continue
                conf = re.sub('\(.*\)','',config_name)
                conf = re.sub('pp[0-9]*','',conf)
                conf = re.sub('tunnel[0-9]*','',conf)
                conf = conf.replace("#","")
                conf = conf.replace(">","")
                with open(file_place + conf + "_" + configname_list[0] + ".txt", mode="a", encoding=character_code['encoding']) as f:
                    if flag is True:
                        f.write(prev_line)
                        flag = False
                    f.write(line)
        os.makedirs(file_place + "\work", exist_ok=True)
        shutil.move(ad_filename , file_place + "\work")
        shutil.move(ex_filename , file_place + "\work")
        shutil.move(file_place + configname_list[0] + osfilename , file_place + "\work")
    except Exception:
        return state + 3
    return 0
