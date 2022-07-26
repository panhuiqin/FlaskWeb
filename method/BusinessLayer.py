# -*- coding: utf-8 -*-
import re
import time
from collections import Counter

import connect_mysql.ConnectDatabase as Db_connect
import CommonMethod.Message as Msg
import json
import method.RedisOperation as Rd


class ExecuteBusiness:
    """
    执行sql业务操作
    """

    def __init__(self):
        self.cursor, self.db = Db_connect.ConnectMysql().MysqlReadingWrite()

    def __del__(self):
        """
        关闭数据库连接池
        :return:
        """
        # print("销毁对象=================================")
        self.db.close()

    def ScreeningConditions(self):
        """
        获取修改项目的项目名，是否需要修改
        :return:
        """
        sql = "SELECT DISTINCT(app_name) FROM api_case where IsRead = '1' ;"
        self.cursor.execute(sql)
        data_api = self.cursor.fetchall()
        data_list = []
        for i in data_api:
            data_list.append(i[0])
        return {"code": "1", "msg": "操作成功", "data": {"list": data_list}}

    def queryCaseInfo(self, isChange, app_name, apiPath, apiCase, apiRelate, pageIndex, pageSize):
        """
        获取修改项目的项目名，是否需要修改
        :return:
        """
        # pageIndex = 5
        # pageSize = 20
        sql_count = "SELECT COUNT(*) FROM api_case WHERE Ischange = '{0}' AND IsRead = '1' AND app_name = '{1}' AND api_path LIKE '%{2}%' AND info_Relate LIKE '%{3}%' ".format(
            isChange, app_name, apiPath, str(apiRelate))
        sql = "SELECT case_seq,case_title,app_name,api_name,api_path,parameter,response, info_Relate,remarks FROM api_case WHERE Ischange = '{0}' AND IsRead = '1' AND app_name = '{1}' AND api_path LIKE '%{2}%' AND info_Relate LIKE '%{3}%' ".format(
            isChange, app_name, apiPath, str(apiRelate))
        if apiCase != "" and apiCase is not None:
            sql_count = "SELECT COUNT(*) FROM api_case WHERE" + " case_seq = '" + apiCase + "'"
            sql = "SELECT case_seq,case_title,app_name,api_name,api_path,parameter,response, info_Relate,remarks FROM api_case WHERE" + " case_seq = '" + apiCase + "'"
            # sql = sql + " and case_seq = '"+ apiCase +"'"
            # sql_count = sql_count + " and case_seq = '"+ apiCase +"'"

        elif apiRelate != "" and apiRelate is not None:
            sql_count = "SELECT COUNT(*) FROM api_case WHERE info_Relate LIKE '%{0}%' ".format(apiRelate)
            sql = "SELECT case_seq,case_title,app_name,api_name,api_path,parameter,response, info_Relate,remarks FROM api_case WHERE info_Relate LIKE '%{0}%' ".format(
                apiRelate)
        if pageIndex is None and pageSize is None:
            sql = sql + " limit 0,20"
        else:
            pageIndex = (int(pageIndex) - 1) * int(pageSize)
            sql = sql + " limit {0},{1}".format(pageIndex, pageSize)
        # print(sql)

        self.cursor.execute(sql)
        data_api = self.cursor.fetchall()

        self.cursor.execute(sql_count)
        total_count = self.cursor.fetchall()

        data_list = []
        # print(sql)
        for i in data_api:
            data_list.append(i)
        return {"code": "1", "msg": "操作成功", "total": total_count[0][0], "data": {"list": data_list}}

    def DeleteCase(self, postData):
        """
        删除不要的用例，isRead改成0
        :return:
        """
        # sql = "SELECT * FROM api_case WHERE case_seq = '{0}';".format(postData)
        sql = "UPDATE api_case SET IsRead = '0' WHERE case_seq = '{0}';".format(postData)
        self.cursor.execute(sql)
        self.db.commit()
        return {"code": "1", "msg": "操作成功"}

    def queryCaseAllInfo(self, postData):
        """
        获取修改项目的项目名，是否需要修改
        :return:
        """
        sql = "SELECT * FROM api_case WHERE case_seq = '{0}';".format(postData)
        self.cursor.execute(sql)
        data_api = self.cursor.fetchall()

        sql2 = "SELECT id,parameter_name,case_seq,source, expression FROM case_operate WHERE case_seq = '{0}';".format(
            postData)
        self.cursor.execute(sql2)
        data_api2 = self.cursor.fetchall()
        case_operate_list = []
        for i in data_api2:
            case_operate_list_data = {"id": i[0], "parameterName": i[1], "source": i[3], "expression": i[4]}
            case_operate_list.append(case_operate_list_data)

        data_list = data_api[0]
        data = {
            "caseId": data_list[0],
            "appName": data_list[2],
            "apiType": data_list[3],
            "apiHost": data_list[6],
            "apiPath": data_list[7],
            "parameter": data_list[8],
            "response": data_list[9],
            "case_level": data_list[18],
            "remarks": data_list[15],
            "caseTitle": data_list[16],
            "parameter_type": data_list[17],
            "case_operate": case_operate_list
        }
        return {"code": "1", "msg": "操作成功", "data": data}

    def submitDelete(self, postData):
        """
        提交删除数据的接口
        :return:
        """
        sql = "UPDATE  api_case SET IsRead = '0' WHERE case_seq = '{}'".format(postData)
        self.cursor.execute(sql)
        self.db.commit()  # 不能省，必须要加commit来提交到mysql中去确认执行
        return {"code": "1", "msg": "删除成功"}

    def submitUpdateData(self, case_seq, parameter, response, caseLevel, caseTitle, parameter_type,
                         extract_parameters=None):
        """
        提交更新数据的接口
        :return:
        """
        # parameter = parameter.replace('\"', '\\"')
        # 匹配 ${param} 格式参数变量 判断当前用例等级
        param_pattern = re.compile(r'\${\w+}')
        param_dict = eval(parameter)
        match_ls = []
        for k, v in param_dict.items():
            match_ls = param_pattern.findall(str(v))
            param_str = match_ls[0] if len(match_ls) > 0 else None
            if param_str:
                param = param_str[2:len(param_str) - 1]
                compare_sql = 'select ac.case_seq,ac.case_level from case_operate co JOIN api_case ac on co.case_seq = ac.case_seq where co.parameter_name = %s;'
                self.cursor.execute(compare_sql, param)
                compare_data = self.cursor.fetchall()
                if len(compare_data) == 0:
                    return {'code': '99', 'msg': '当前引用变量“' + param + '”不存在，请修改后重新提交'}
                elif len(compare_data) > 0:
                    # compare_caseSeq = compare_data[0][0]
                    compare_caseLevel = compare_data[0][1]
                    # ASCII码 A<Z
                    if compare_caseLevel >= caseLevel:
                        return {'code': '99', 'msg': '当前用例等级应低于' + compare_caseLevel + '，请修改后重新提交'}

        if extract_parameters is not None:
            sql1 = "SELECT id FROM `case_operate`  WHERE case_seq = %s"
            self.cursor.execute(sql1, case_seq)
            data_api2 = self.cursor.fetchall()
            data_api_list = []
            for i in data_api2:
                data_api_list.append(str(i[0]))
            # 历史的
            data_api_list = tuple(data_api_list)

            # 判断出参名唯一不重复
            # 获取已有的
            former_param_sql = ''
            former_param_tup = ()
            former_param_ls = []
            if len(data_api_list) == 0:
                former_param_sql = 'select distinct(parameter_name) from case_operate;'
                self.cursor.execute(former_param_sql)
            elif len(data_api_list) == 1:
                former_param_sql = 'select distinct(parameter_name) from case_operate where id != {0};'.format(
                    data_api_list[0])
                self.cursor.execute(former_param_sql)
            elif len(data_api_list) > 1:
                former_param_sql = 'select distinct(parameter_name) from case_operate where id not in {0};'.format(
                    data_api_list)
                self.cursor.execute(former_param_sql)
            former_param_tup = self.cursor.fetchall()
            for param in former_param_tup:
                former_param_ls.append(param[0])
            # 新提交的
            current_param_ls = []
            for l in extract_parameters:
                current_param_ls.append(l['parameterName'])
            # 判断新提交有无重复
            param_dict = dict(Counter(current_param_ls))
            if len([k for k, v in param_dict.items() if v > 1]) > 0:
                return {'code': '99', 'msg': '当前出参名称有重复，请修改后重新提交'}
            else:
                # 历史出参变量名 交 当前提交变量名 取交集
                param_set = list(set(former_param_ls) & set(current_param_ls))
                if len(param_set) == 0:
                    # 先判断 后插入
                    sql = "UPDATE api_case SET parameter = %s,response = %s, Ischange = '0', case_level= %s, case_title= %s, parameter_type = %s WHERE case_seq = %s"
                    self.cursor.execute(sql, (parameter, response, caseLevel, caseTitle, parameter_type, case_seq))
                    self.db.commit()

                    for l in extract_parameters:
                        sql2 = "INSERT INTO `case_operate`(`id`, `case_seq`, `parameter_name`, `source`, `expression`) VALUES (NULL,%s, %s, %s, %s);"
                        self.cursor.execute(sql2, (case_seq, l["parameterName"], l["source"], l["expression"]))
                        self.db.commit()

                    if data_api_list:
                        if len(data_api_list) == 1:
                            sql3 = "DELETE FROM case_operate WHERE id = %s"
                            self.cursor.execute(sql3, data_api_list[0])
                            self.db.commit()
                        else:
                            sql3 = "DELETE FROM case_operate WHERE id in {0}".format(data_api_list)
                            self.cursor.execute(sql3)
                            self.db.commit()
                elif len(param_set) > 0:
                    param_str = ''
                    for param in param_set:
                        param_str = param_str + '“' + str(param) + '”、'
                    param_str = param_str.rstrip('、')
                    return {'code': '99', 'msg': '变量名称：' + param_str + '重复，请修改后重新提交'}
        return {"code": "1", "msg": "修改成功"}

    def submitInsertData(self, case_seq, parameter, response, caseLevel, caseTitle, parameter_type, extract_parameters):
        """
        提交插入数据的接口
        :return:
        """
        # 匹配 ${param} 格式参数变量 判断当前用例等级
        param_pattern = re.compile(r'\${\w+}')
        param_dict = eval(parameter)
        match_ls = []
        for k, v in param_dict.items():
            print(k,v)
            match_ls = param_pattern.findall(str(v))
            param_str = match_ls[0] if len(match_ls) > 0 else None
            if param_str:
                param = param_str[2:len(param_str) - 1]
                compare_sql = 'select ac.case_seq,ac.case_level from case_operate co JOIN api_case ac on co.case_seq = ac.case_seq where co.parameter_name = %s;'
                self.cursor.execute(compare_sql, param)
                compare_data = self.cursor.fetchall()
                if len(compare_data) == 0:
                    return {'code': '99', 'msg': '当前引用变量“' + param + '”不存在，请修改后重新提交'}
                elif len(compare_data) > 0:
                    # compare_caseSeq = compare_data[0][0]
                    compare_caseLevel = compare_data[0][1]
                    # ASCII码 A<Z
                    if compare_caseLevel >= caseLevel:
                        return {'code': '99', 'msg': '当前用例等级应低于' + compare_caseLevel + '，请修改后重新提交'}

        if extract_parameters is not None:
            # 判断出参名唯一不重复
            # 获取已有的
            former_param_sql = 'select distinct(parameter_name) from case_operate;'
            former_param_tup = ()
            former_param_ls = []
            self.cursor.execute(former_param_sql)
            former_param_tup = self.cursor.fetchall()
            for param in former_param_tup:
                former_param_ls.append(param[0])

            # 新提交的
            current_param_ls = []
            for l in extract_parameters:
                current_param_ls.append(l['parameterName'])
            # 判断新提交有无重复
            param_dict = dict(Counter(current_param_ls))
            if len([k for k, v in param_dict.items() if v > 1]) > 0:
                return {'code': '99', 'msg': '当前出参名称有重复，请修改后重新提交'}
            else:
                # 取交集
                param_set = list(set(former_param_ls) & set(current_param_ls))
                if len(param_set) == 0:
                    sql = "insert into api_case(case_seq,api_id, app_name,api_type,request_type,api_name,api_host,api_path,parameter, response, Ischange, IsRead,auth_type, actual_value, case_level, remarks, case_title, parameter_type) " \
                          "SELECT  NULL case_seq,api_id, app_name,api_type,request_type,api_name,api_host,api_path,%s parameter,%s response,'0' Ischange,'1' IsRead,auth_type, actual_value, %s info_Relate, remarks, %s case_title, %s parameter_type " \
                          "FROM api_case WHERE case_seq = %s"
                    sql_id = "SELECT last_insert_id();"
                    self.cursor.execute(sql, (parameter, response, caseLevel, caseTitle, parameter_type, case_seq))
                    self.cursor.execute(sql_id)
                    new_id = self.cursor.fetchall()
                    new_case_id = new_id[0][0]
                    self.db.commit()

                    for l in extract_parameters:
                        sql2 = "INSERT INTO `case_operate`(`id`, `case_seq`, `parameter_name`, `source`, `expression`) VALUES (NULL,%s, %s, %s, %s);"
                        self.cursor.execute(sql2, (new_case_id, l["parameterName"], l["source"], l["expression"]))
                        self.db.commit()

                elif len(param_set) > 0:
                    param_str = ''
                    for param in param_set:
                        param_str = param_str + '“' + str(param) + '”、'
                    param_str = param_str.rstrip('、')
                    return {'code': '99', 'msg': '变量名称：' + param_str + '重复，请修改后重新提交'}
        return {"code": "1", "msg": "插入成功"}

    def Home(self):
        """
        首页
        :return:
        """
        sql = "SELECT case_seq,app_name,api_type,request_type,api_name,api_host,api_path,parameter,response,auth_type FROM api_case WHERE Ischange = '1' AND IsRead = '1'"
        self.cursor.execute(sql)
        data_api = self.cursor.fetchall()
        return data_api

    def getCaseInfo(self, postData):
        """
        通过用例id放回用例详情
        :return:
        """
        sql = "SELECT case_seq,parameter,expect_value FROM api_case WHERE case_seq = '{}'".format(postData)
        self.cursor.execute(sql)
        data_api = self.cursor.fetchall()
        return {"caseId": data_api[0], "parameter": data_api[0], "expectValue": data_api[0]}

    def update_case_table(self):
        """
        更新用例表，获取最新的接口用例数据
        :return:
        """
        """
        修改用例表的IsRead，Ischange字段，改成IsRead=0，Ischange=0，条件：用例表的api_id不存在接口表中
        """

        def modify(data_url, data_cases):
            """
            判断是否需要修改
            :return:是否修改
            """
            # 接收接口表的数据，返回一个字典{"api_id":"data"}
            url_list = list(data_url)
            url_dict = dict(url_list)
            # 接收用例表的数据，返回一个字典{"api_id":"data"}
            cases_list = list(data_cases)
            # print(cases_list)
            # cases_dict = dict(cases_list)
            # 新建一个接收需要修改的列表
            tup_change = []
            # 新建一个接收不需要修改的列表
            tup_Nochange = []
            for i in cases_list:
                cases_path = i[0]  # 路径
                api_body = i[1]  # 请求体
                cases_id = i[2]  # 用例id
                # 获取接口表单个接口body的内容，dict
                # print(cases_id)
                if url_dict[cases_path] == "":
                    url_dict_i_dict = ""
                else:
                    try:
                        url_dict_i_dict = json.loads(url_dict[cases_path])
                    except:
                        url_dict_i_dict = ""

                # 获取用例表单个接口body的内容，dict
                if api_body == "":
                    case_dict_i_dict = ""
                else:
                    try:
                        case_dict_i_dict = json.loads(api_body)
                    except:
                        case_dict_i_dict = ""

                # 新建一个需要修改的元组
                if isinstance((case_dict_i_dict, url_dict_i_dict), dict) and set(
                        dict(case_dict_i_dict).keys()).issubset(set(dict(url_dict_i_dict).keys())):
                    tup_Nochange.append(cases_id)

                # 不是对象类型，不作修改
                elif isinstance((case_dict_i_dict, url_dict_i_dict), int):
                    tup_Nochange.append(cases_id)

                else:
                    tup_change.append(cases_id)
            tup_change_tup1 = tuple(tup_change)
            tup_Nochange_tup1 = tuple(tup_Nochange)
            # print(tup_change_tup1)
            # print(tup_Nochange_tup1)
            return tup_change_tup1, tup_Nochange_tup1

        # 去掉不要的接口
        # sql_url_del = "UPDATE api_info A RIGHT JOIN api_case B ON B.api_id=A.api_id SET B.IsRead='0', B.Ischange='1' WHERE A.api_path IS NULL"
        sql_url_del = "UPDATE  api_info A RIGHT JOIN api_case B ON B.api_id=A.api_id SET B.IsRead=0 WHERE A.api_path IS NULL"
        self.cursor.execute(sql_url_del)
        self.db.commit()  # 不能省，必须要加commit来提交到mysql中去确认执行

        """
        修改用例表的IsRead，Ischange字段，改成IsRead=1，Ischange=1，条件：用例表的api_id存在table表中
        并且判断存在的用例是否需要修改body
        """
        # 修改接口表有，用例表有，但状态IsRead=0，的接口
        sql_url_add = "UPDATE api_info a inner join api_case b on B.api_id=A.api_id SET b.IsRead = '1' WHERE b.IsRead = '0';"
        self.cursor.execute(sql_url_add)
        self.db.commit()  # 不能省，必须要加commit来提交到mysql中去确认执行

        """
        修改用例表的IsRead，Ischange字段，改成IsRead=1，Ischange=1，条件：接口表中有的api_id，用例表中没有对应api_id
        """
        Relate = {"level": "关联用例等级", "type": "1",
                  "contact": {"关联用例id": {"inq（关联用例的参数）": "inq（接口返回的参数）", "docName（关联用例的参数）": "docName（接口返回的参数）"}}}
        Relate = json.dumps(Relate, ensure_ascii=False)
        sql_url_change = "insert into api_case(case_seq, api_id, app_name,api_type,request_type,api_name,api_host,api_path,parameter,response,Ischange,IsRead,auth_type, actual_value, info_Relate, remarks, parameter_type, '用例等级' case_level, '0' case_scenario) SELECT case_seq, A.api_id, A.app_name,A.api_type,A.request_type,A.api_name,A.api_host,A.api_path,A.parameter,A.response,'1' Ischange,'1' IsRead,A.auth_type, '' actual_value, %s info_Relate, A.remarks, 1 parameter_type, '用例等级' case_level, '0' case_scenario FROM  api_info A LEFT JOIN api_case B ON A.api_id = B.api_id WHERE B.api_id IS NULL;"
        self.cursor.execute(sql_url_change, Relate)
        self.db.commit()  # 不能省，必须要加commit来提交到mysql中去确认执行
        # 关闭数据库连接

        try:

            # 查询接口表需要执行的接口
            sql_url = "select api_id,parameter from api_info;"
            self.cursor.execute(sql_url)
            data_api = self.cursor.fetchall()
            # 查询用例表需
            # sql_casc = "SELECT api_id,parameter,case_seq FROM api_case WHERE IsRead='1';"
            sql_casc = "SELECT api_id,parameter,case_seq FROM api_case WHERE IsRead='1' AND Ischange = '0';"
            self.cursor.execute(sql_casc)
            data_case = self.cursor.fetchall()
            tup_change_tup, tup_Nochange_tup = modify(data_url=data_api, data_cases=data_case)
            # print( tup_Nochange_tup)
            # print(tup_change_tup)
            # 更新是否需要修改的数据

            if len(tup_change_tup) == 0:
                print("不需要修改")
            elif len(tup_change_tup) == 1:
                tup_change_tup_update = "UPDATE api_case SET Ischange='1' WHERE case_seq = '{0}'".format(
                    tup_change_tup[0])
                self.cursor.execute(tup_change_tup_update)
            elif len(tup_change_tup) > 1:
                tup_change_tup_update = "UPDATE api_case SET Ischange='1' WHERE case_seq in {0}".format(tup_change_tup)
                self.cursor.execute(tup_change_tup_update)
            return {"code": "1", "msg": "更新成功"}

        except:
            # 通知企业微信机器人。更新项目，更新用例出现错误
            Msg.MessageNotification().msg_qw_case()
            return {"code": "1", "msg": "更新成功，用例状态更新失败"}

    def getCaseExecute(self, caseId=None, appName=None, scenceId=None):
        """
        获取需要执行的用例
        :parameter: scenceId
        :return:
        """
        if caseId is not None:
            api_list = [1, 1]
            if isinstance(caseId, (str, int)):
                # api_list = [1, 1]
                sql = "select CONCAT(IFNULL(case_level,''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq =%s "
                self.cursor.execute(sql, caseId)
                results = self.cursor.fetchall()
                print(list(results))
                return list(results), list(api_list)

            elif isinstance(caseId, list):
                if len(caseId) == 1:
                    sql2 = "select CONCAT('场景', IFNULL(case_scenario,''), '-用例id',case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq = %s"
                    self.cursor.execute(sql2, caseId[0])
                    results_list = self.cursor.fetchall()
                    return list(results_list), list(api_list)
                else:
                    results_tuple = tuple(caseId)
                    sql2 = "select CONCAT('场景', IFNULL(case_scenario,''), '-用例id', case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq in {0} ".format(
                        results_tuple)
                    self.cursor.execute(sql2)
                    results_list = self.cursor.fetchall()
                    return list(results_list), list(api_list)

                # sql = "select CONCAT(IFNULL(case_level,''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq =%s "
                # self.cursor.execute(sql, caseId)
                # results = self.cursor.fetchall()
                # print(list(results))
                # return list(results), list(api_list)

        elif scenceId is not None:
            api_list = [1, 1]
            sql = "SELECT case_seq FROM interface_scenario WHERE scence_id = %s"
            self.cursor.execute(sql, scenceId)
            results1 = self.cursor.fetchall()
            results_list = results1[0][0]
            # 判断场景是否存在用例
            if results_list is None :
                return results_list, list(api_list)
            results_list = results_list[1:-1].split(",")
            if len(results_list) == 1:
                sql2 = "select CONCAT(IFNULL(case_level,''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq = %s"
                self.cursor.execute(sql2, results_list[0])
                results = self.cursor.fetchall()
            else:
                results_tuple = tuple(results_list)
                print(results_tuple)
                sql2 = "select CONCAT(IFNULL(case_level,''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq in {0} ".format(
                    results_tuple)
                self.cursor.execute(sql2)
                results = self.cursor.fetchall()
            return list(results), list(api_list)

        elif appName is not None:
            sql_api_count = "SELECT COUNT(api_id) FROM api_info where app_name = %s ;"
            sql_api_execute = "SELECT COUNT(DISTINCT api_id) FROM api_case WHERE Ischange = '0' AND IsRead = '1' AND app_name = %s ;"
            # sql = "select CONCAT(REPLACE(json_extract(info_Relate,'$.level'),'{}',''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq FROM api_case WHERE Ischange = '0' AND IsRead = '1' and app_name = %s".format('"')
            # 获取单项目的单接口用例
            sql = "select CONCAT(IFNULL(case_level,''), case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE Ischange = '0' AND IsRead = '1' and app_name = %s and case_scenario = '0'"
            api_list = []
            try:
                # 执行sql语句
                self.cursor.execute(sql_api_count, appName)
                api_count = self.cursor.fetchall()
                api_list.append(api_count[0][0])

                self.cursor.execute(sql_api_execute, appName)
                api_execute = self.cursor.fetchall()
                api_list.append(api_execute[0][0])

                # 获取所有的记录
                self.cursor.execute(sql, appName)
                results = self.cursor.fetchall()

                # 获取关联接口用例
                # case_list = ExecuteBusiness().get_case_data(appName)
                # case_tuple = tuple(case_list)
                # if case_tuple :
                #     sql_1 = "select CONCAT(case_level, case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq in {0} ".format(case_tuple)
                #     self.cursor.execute(sql_1)
                #     api_execute_1 = self.cursor.fetchall()
                # else:
                #     api_execute_1 = case_tuple

                # 获取场景关联用例id
                sql_scence = "SELECT case_seq, scence_id FROM interface_scenario WHERE app_name = %s"
                self.cursor.execute(sql_scence, appName)
                case_scence = self.cursor.fetchall()
                scence_case_list = []
                for l in case_scence:
                    results_list_1 = l[0]
                    if results_list_1:
                        results_list_1 = results_list_1[1:-1].split(",")
                        scence_case_list = scence_case_list + results_list_1

                # 获取用例场景对应的用例详情
                if scence_case_list == 1:
                    sql2 = "select CONCAT('场景', IFNULL(case_scenario,''), '-用例id',case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq = %s"
                    self.cursor.execute(sql2, scence_case_list[0])
                    results_list = self.cursor.fetchall()
                else:
                    results_tuple = tuple(scence_case_list)
                    sql2 = "select CONCAT('场景', IFNULL(case_scenario,''), '-用例id', case_seq) acn, app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario FROM api_case WHERE case_seq in {0} ".format(
                        results_tuple)
                    self.cursor.execute(sql2)
                    results_list = self.cursor.fetchall()
                print(results_list)

                results_all = list(results) + list(results_list)
                return results_all, list(api_list)
            except:
                print("getData Error!")

        else:
            sql_api_count = "SELECT COUNT(api_id) FROM api_info;"
            sql_api_execute = "SELECT COUNT(DISTINCT api_id) FROM api_case WHERE Ischange = '0' AND IsRead = '1';"
            sql = "select CASE WHEN case_scenario = '0' THEN  CONCAT(IFNULL(case_level,''),IFNULL(case_seq,'') ) ELSE  CONCAT('场景', IFNULL(case_scenario,''), '-用例id', case_seq) END acn , app_name, api_type, api_name, api_host, api_path, request_type, parameter, response, actual_value, auth_type, info_Relate, case_seq,case_title, parameter_type, case_level, case_scenario from api_case WHERE Ischange = '0' AND IsRead = '1'"  # and app_name in ('hosptial','fzdoctor' ) and case_seq in ('7407')
            api_list = []
            try:
                # 执行sql语句
                self.cursor.execute(sql_api_count)
                api_count = self.cursor.fetchall()
                api_list.append(api_count[0][0])

                self.cursor.execute(sql_api_execute)
                api_execute = self.cursor.fetchall()
                api_list.append(api_execute[0][0])

                # 获取所有的记录
                self.cursor.execute(sql)
                results = self.cursor.fetchall()
                return list(results), list(api_list)
            except:
                print("getData Error!")

    def update(self, case_id, result1):
        query = "UPDATE api_case SET actual_value = '{0}' WHERE case_seq= '{1}'".format(result1, case_id)
        sql1 = "SELECT actual_value FROM api_case WHERE case_seq = '{}'".format(case_id)
        self.cursor.execute(query)
        self.db.commit()
        self.cursor.execute(sql1)
        # 获取所有的记录
        results = self.cursor.fetchall()
        # 打印表数据
        for row in results:
            # print(row)
            api_name = row[0]
            # print(eval(result1), api_name)
            if api_name == result1:
                print("用例表数据库更新成功")
            else:
                print("update Error!")

    def get_token_headers(self):
        """
        获取项目信息
        :return:
        """
        sql = "select app_name, headers, auth_type, request_type, url, body from pro_info;"
        self.cursor.execute(sql)
        ab = self.cursor.fetchall()
        return ab

    def upward_query_case(self, caseId_list, all_list):
        """
        向上找
        :return:
        """
        if caseId_list:
            for caseId in caseId_list:
                sql = "SELECT case_seq FROM `api_case`  WHERE info_Relate like '%{0}%'".format(caseId)
                self.cursor.execute(sql)
                ab = self.cursor.fetchall()
                # print(ab)
                if ab:
                    # 判断查出来的数据是否是主流程用例
                    qwe = []
                    for l in ab:
                        dict_l = str(l[0])
                        # 判断
                        sql = "SELECT REPLACE(json_extract(info_Relate,'$.type'),'{0}','') FROM `api_case`  WHERE case_seq = %s".format(
                            '"')
                        self.cursor.execute(sql, dict_l)
                        abc = self.cursor.fetchall()
                        if abc:
                            if str(abc[0][0]) == '2':
                                qwe.append(dict_l)
                            else:
                                continue
                        else:
                            continue
                    all_list = qwe + all_list
                    all_list = ExecuteBusiness().upward_query_case(qwe, all_list)
                else:
                    continue
            return all_list
        else:
            return all_list

    def downward_query_case(self, caseId_list, all_list):
        """
        向下找
        :return:
        """
        if caseId_list:
            for caseId in caseId_list:
                sql = "SELECT info_Relate FROM `api_case`  WHERE REPLACE(json_extract(info_Relate,'$.type'),'{0}','') = '2' and case_seq = %s".format(
                    '"')
                self.cursor.execute(sql, caseId)
                ab = self.cursor.fetchall()
                if ab:
                    # 循环获取每个用例
                    for l in ab:
                        dict_l = json.loads(l[0])
                        if 'contact' in dict_l.keys():
                            dict_list1 = dict_l['contact']
                            dict_list = [*dict_list1]

                            # 判断查出来的数据是否是主流程用例
                            for K in dict_list:
                                sql = "SELECT REPLACE(json_extract(info_Relate,'$.type'),'{0}','') FROM `api_case`  WHERE case_seq = %s".format(
                                    '"')
                                self.cursor.execute(sql, K)
                                ab = self.cursor.fetchall()
                                if ab:
                                    if str(ab[0][0]) == '2':
                                        continue
                                    else:
                                        dict_list.remove(K)
                                else:
                                    dict_list.remove(K)

                            # 移除默认的用例数据，关联用例id
                            if '关联用例id' in dict_list:
                                dict_list.remove('关联用例id')
                            all_list = all_list + dict_list
                            all_list = ExecuteBusiness().downward_query_case(dict_list, all_list)
                else:
                    continue

            return all_list
        else:
            return all_list

    def get_case_data(self, appName):
        """
        获取项目信息
        :return:
        """
        sql = "SELECT case_seq FROM `api_case`  WHERE REPLACE(json_extract(info_Relate,'$.type'),'{}','') = '2' and app_name = %s ;".format(
            '"')
        self.cursor.execute(sql, appName)
        ab = self.cursor.fetchall()

        # 处理查询到的用例数据
        case_list = []
        for i in ab:
            case = i[0]
            case_list.append(str(case))
        case_1 = ExecuteBusiness().upward_query_case(case_list, case_list)
        case_2 = ExecuteBusiness().downward_query_case(case_list, case_list)

        case_list = case_1 + case_2
        case_list = list(set(case_list))
        return case_list

    def get_case_extract_data(self, caseId):
        """
        获取关联用例的信息
        :param caseId: 查询用用例id
        :return:
        """
        # caseId = "1385"
        sql = "SELECT parameter FROM `api_case`  WHERE case_seq = %s "
        self.cursor.execute(sql, caseId)
        ab = self.cursor.fetchall()
        parameter_data = ab[0][0]
        print(ab)
        parameter_data_list = list(json.loads(parameter_data).keys())
        # print(parameter_data)
        # print(parameter_data_list)
        return parameter_data_list

    def submitInsertData1(self):
        """
        提交插入数据的接口
        :return:
        """
        sql = 'INSERT INTO `jmeter_test`.`case_operate`(`id`, `case_seq`, `parameter_name`, `source`, `expression`) VALUES (NULL,"123", "123", "123", "ces");'
        sql_id = "SELECT last_insert_id();"
        self.cursor.execute(sql)
        self.cursor.execute(sql_id)
        ab = self.cursor.fetchall()
        self.db.commit()
        print(ab)

    # ExecuteBusiness().submitInsertData1()

    def queryProEnum(self):
        """
        查询所有pro 枚举值
        :return:
        """
        sql = "select distinct(app_name) from pro_info ;"
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        pro_ls = []
        auth_dict = {'外部认证': '1', '内部认证': '2', '商家后台': '3'}
        for i in data:
            pro_ls.append(i[0])
        data = {'proName': pro_ls, 'authType': auth_dict}
        return {"code": "1", "msg": "操作成功", "data": data}

    def queryProInfo(self, proName):
        """
        查询完整项目信息
        :return:
        """
        sql = "select * from pro_info where app_name like %s;"
        self.cursor.execute(sql, proName)
        data = self.cursor.fetchall()
        proInfo = {'proName': data[0][0], 'proDeclare': data[0][6], 'reqHeader': data[0][1], 'reqUrl': data[0][2],
                   'reqType': data[0][3], 'authType': data[0][4], 'secretKey': data[0][5], 'reqBody': data[0][7],
                   'certification': data[0][8]}
        return {'code': '1', 'msg': '操作成功', 'data': proInfo}

    def addOrEditProInfo(self, state, params):
        """
        新增/编辑项目信息
        :return:
        """
        for param, value in params.items():
            if (param in ['proName', 'reqHeader', 'reqUrl', 'reqType', 'proDeclare', 'certification', 'reqBody']):
                if value == None or value == '' or value == 'null':
                    return {'code': '1001', 'msg': '当前存在必填项未填写，请填写后重新提交'}
        if state != None:
            if state == '0':
                proName_ls = ExecuteBusiness().queryProEnum()['data']['proName']
                if params['proName'] in proName_ls:
                    return {'code': '1001', 'msg': '当前项目信息已存在'}
                else:
                    sql = 'insert into pro_info (app_name,headers,url,request_type,auth_type,`sercert_key/iv`,name,body,Certification) values(%s,%s,%s,%s,%s,%s,%s,%s,%s); '
                    self.cursor.execute(sql, (
                    params['proName'], params['reqHeader'], params['reqUrl'], params['reqType'], params['authType'],
                    params['secretKey'], params['proDeclare'], params['reqBody'], params['certification']))
            elif state == '1':
                sql = 'update pro_info set headers=%s,url=%s,request_type=%s,auth_type=%s,`sercert_key/iv`=%s, name = %s,body=%s,Certification=%s where app_name = %s;'
                self.cursor.execute(sql, (
                params['reqHeader'], params['reqUrl'], params['reqType'], params['authType'], params['secretKey'],
                params['proDeclare'], params['reqBody'], params['certification'], params['proName']))
        self.db.commit()
        return {'code': '1', 'msg': '操作成功'}

    def caseInfo(self, caseSeq):
        """
        查询单个接口用例详情
        :param caseSeq:
        :return:
        """
        sql = "select * from `api_case` where case_seq = %s;"
        self.cursor.execute(sql, caseSeq)
        data = self.cursor.fetchall()
        caseInfo = {'case_seq': data[0][0], 'app_name': data[0][2], 'api_path': data[0][7],
                    'request_type': data[0][4], 'remarks': data[0][15], 'case_title': data[0][16]}
        return caseInfo

    def sceInfoList(self, params, pageIndex, pageSize):
        """
        场景用例列表
        :param params:
        :return:
        """
        params_ls = []
        scenceInfo = []
        if len(params) == 0:
            sql = 'select * from `interface_scenario` where isDelete = "1"'
            # 总条数
            sql_total = sql.replace('*', 'count(*)')
            self.cursor.execute(sql_total)
            result_total = self.cursor.fetchall()
            # 分页条数
            limit_start = (int(pageIndex) - 1) * int(pageSize)
            sql_limit = sql + ' limit %s,%s ;' % (limit_start, pageSize)
            self.cursor.execute(sql_limit)
            result_limit = self.cursor.fetchall()
        elif len(params) > 0:
            sql = 'select * from `interface_scenario` where is_delete = "1" and'
            for k, v in params.items():
                sql = sql + " %s like " % (k)
                sql = sql + '%s and'
                if k == 'scence_id':
                    params_ls.append('%' + v + '%')
                else:
                    params_ls.append(v)
            sql = sql.rstrip('and')
            # 总条数
            sql_total = sql.replace('*', 'count(*)')
            self.cursor.execute(sql_total, params_ls)
            result_total = self.cursor.fetchall()
            # 分页条数
            limit_start = (int(pageIndex) - 1) * int(pageSize)
            sql_limit = sql + ' order by `scence_id` desc limit %s,%s ;' % (limit_start, pageSize)
            self.cursor.execute(sql_limit, params_ls)
            result_limit = self.cursor.fetchall()
        # 返回
        for item in result_limit:
            scenceInfo.append(
                {'scence_id': item[0], 'app_name': item[1], 'scence_name': item[2], 'scence_level': item[4],
                 'scence_state': item[3], 'step_no': item[5], 'scence_describe': item[7]})
        return {'code': '1', 'msg': '操作成功', 'total': result_total[0][0], 'data': scenceInfo}

    def querySceInfo(self, sceId):
        """
        场景用例详情 精确
        :param sceId:
        :return:
        """
        sql = "select * from `interface_scenario` where scence_id like %s;"
        self.cursor.execute(sql, str(sceId))
        data = self.cursor.fetchall()
        sceInfo = {'scence_id': data[0][0], 'app_name': data[0][1], 'scence_name': data[0][2],
                   'scence_level': data[0][4], 'scence_state': data[0][3], 'scence_describe': data[0][7],
                   'step_no': data[0][5]}
        # 返回单接口用例
        # eval()去掉参数最外侧引号,变成python可执行的语句
        case_ls = []
        execute = ExecuteBusiness()
        if data[0][6] is not None:
            cases = eval(data[0][6])
            for case in cases:
                data = execute.caseInfo(case)
                case_ls.append(data)
        else:
            case_ls = None
        sceInfo.update({'cases': case_ls})
        return {'code': '1', 'msg': '操作成功', 'data': sceInfo}

    def addOrEditSceInfo(self, state, params):
        """
        新建/编辑场景用例
        :param state:
        :param params:
        :return:
        """
        if state != None:
            if str(state) == '0' or str(state) == '1':
                for param, value in params.items():
                    if (param in ['appName', 'scenceName', 'scenceState']):
                        if value == None or value == '' or value == 'null':
                            return {'code': '1001', 'msg': '当前存在必填项未填写，请填写后重新提交'}
                # 新增场景
                if str(state) == '0':
                    # id
                    sql_max_id = 'select scence_id from `interface_scenario` order by scence_id desc limit 0,1;'
                    self.cursor.execute(sql_max_id)
                    data = self.cursor.fetchall()
                    if len(data) == 0:
                        maxId = 1
                    elif len(data) > 0:
                        maxId = str(int(data[0][0]) + 1)
                    sql = 'insert into `interface_scenario` (`app_name`,`scence_id`,`scence_name`,`scence_state`,`scence_level`,`step NO`,`case_seq`,`is_delete`,`scence_describe`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                    self.cursor.execute(sql, (
                    params['appName'], maxId, params['scenceName'], params['scenceState'], params['scenceLevel'],
                    params['stepNo'], params['caseSeq'], '1', params['scenceDesc']))
                # 编辑场景
                elif state == '1':
                    sql = 'update `interface_scenario` set app_name=%s,scence_name=%s,scence_state=%s,scence_level=%s,scence_describe=%s where scence_id = %s;'
                    self.cursor.execute(sql, (
                    params['appName'], params['scenceName'], params['scenceState'], params['scenceLevel'],
                    params['scenceDesc'], params['scenceId']))
            # 编辑场景用例集
            elif str(state) == '2':
                # 先更新原有接口api_case case_scenario字段 = 0
                former_case_sql = 'select case_seq from `interface_scenario` where scence_id = %s;'
                self.cursor.execute(former_case_sql, params['scenceId'])
                former_case = self.cursor.fetchall()[0][0]
                if former_case is not None and former_case != '':
                    former_case_ls = eval(former_case)
                    if len(former_case_ls) > 0:
                        former_cases_str = '('
                        for cs in former_case_ls:
                            former_cases_str = former_cases_str + str(cs) + ','
                        former_cases_str = former_cases_str.rstrip(',') + ')'
                        update_sql = 'update api_case set case_scenario = "0" where case_seq in %s;' % former_cases_str
                        self.cursor.execute(update_sql)
                        self.db.commit()
                # 清空场景的单接口 修改原有api_case case_scenario字段 = 0
                if params['caseSeq'] == '' or params['caseSeq'] is None:
                    sql = 'update `interface_scenario` set `case_seq` = %s,`step NO` = %s where scence_id = %s;'
                    self.cursor.execute(sql, (None, None, params['scenceId']))
                # 处理新提交的接口 api_case case_scenario字段 = 对应场景id
                elif params['caseSeq'] is not None and params['caseSeq'] != '':
                    case_ls = eval(params['caseSeq'])
                    if len(case_ls) > 0:
                        cases_str = '('
                        for cs in case_ls:
                            cases_str = cases_str + str(cs) + ','
                        cases_str = cases_str.rstrip(',') + ')'
                        update_sql = 'update api_case set case_scenario = %s where case_seq in %s;' % (
                        params['scenceId'], cases_str)
                        self.cursor.execute(update_sql)
                        self.db.commit()
                    sql = 'update `interface_scenario` set `case_seq` = %s,`step NO` = %s where scence_id = %s;'
                    self.cursor.execute(sql, (params['caseSeq'], params['stepNo'], params['scenceId']))
        self.db.commit()
        return {'code': '1', 'msg': '操作成功'}

    def deleteSceInfo(self, sceId):
        """
        删除场景用例 isDelete = 0 存在 idDelete = 1 删除
        :param sceId:
        :return:
        """
        sql = 'update `interface_scenario` set is_delete = "2" where scence_id = %s;'
        self.cursor.execute(sql, sceId)
        self.db.commit()
        return {'code': '1', 'msg': '删除成功'}

    def submittedCases(self, params):
        if len(params) > 0:
            data = []
            for param in params:
                sql = "select * from api_case where case_seq = %s;"
                self.cursor.execute(sql, str(param))
                result = self.cursor.fetchall()
                data.append(result[0])
            return {'code': '1', 'msg': '操作成功', 'data': data}
        else:
            return {'code': '1', 'msg': '操作成功', 'data': []}

    def get_case_operate(self, caseId):
        """
        查询用例提取的参数
        """
        sql = "SELECT case_seq, parameter_name, source,expression FROM case_operate WHERE case_seq = %s"
        self.cursor.execute(sql, caseId)
        ab = self.cursor.fetchall()
        case_operate_list = []
        for i in ab:
            if i[0] is not None and i[1] is not None and i[2] is not None and i[3] is not None:
                case_operate = {"caseId": i[0], "parameterName": i[1], "source": i[2], "expression": i[3]}
                case_operate_list.append(case_operate)
        return case_operate_list


# if __name__ == '__main__':
#     exec = ExecuteBusiness()
