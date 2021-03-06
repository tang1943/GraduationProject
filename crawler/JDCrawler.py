# coding:utf-8
# Author:yunya  Created: 2016/12/6
import pandas as pd
import urllib2
import re
import random
import time
import json
import threading


class JDCrawler(threading.Thread):

    scores = None
    item_ids = None
    crawler_name = "default"
    start_index = -1

    def __init__(self, item_ids_input, scores_input, start_index, name):
        super(JDCrawler, self).__init__()
        self.item_ids = item_ids_input
        self.scores = scores_input
        self.crawler_name = name
        self.start_index = start_index

    @staticmethod
    def jd_html_parse(item_id, score, page_index):
        url = "https://sclub.jd.com/comment/productPageComments.action?productId=" + item_id + "&score=" + str(score) + \
              "&sortType=3&page=" + str(page_index) + "&pageSize=10&callback=fetchJSON_comment98vv37464"
        try:
            req = urllib2.urlopen(url)
        except Exception, e:
            print e
            return []
        origin_encode = req.headers['content-type'].split('charset=')[-1]
        try:
            html = req.read().decode(origin_encode).encode("utf-8")
            groups = re.findall("(?<=fetchJSON_comment98vv37464\().*(?=\);)", html)
            return [json.loads(group, encoding="utf-8") for group in groups]
        except Exception, e:
            print e
            return []

    def run(self):
        item_ids_to_crawler = self.item_ids[self.start_index:]
        for item_id in item_ids_to_crawler:
            print "%s crawler item%d" % (self.crawler_name, self.start_index)
            # 采集第一个关于各种评论的数量
            first_page = self.jd_html_parse(item_id, self.scores[0], 0)
            if len(first_page) < 1:
                continue
            page_count = min(
                first_page[0]["productCommentSummary"]["goodCount"] / 10,
                first_page[0]["productCommentSummary"]["generalCount"] / 10,
                first_page[0]["productCommentSummary"]["poorCount"] / 10)
            page_count = page_count if page_count < 150 else 150
            comments_storage, scores_storage = [], []
            useful_vote_storage, useless_vote_storage = [], []
            reply_count_storage, image_count_storage = [], []
            user_level_storage, father_ids, ids = [], [], []
            for score in self.scores:
                print "Get score=%d" % score
                for page_index in range(page_count):  # 12.13 edit
                    for json_item in self.jd_html_parse(item_id, score, page_index):
                        try:
                            for comment in json_item["comments"]:
                                father_ids.append(item_id)
                                ids.append(comment["id"])
                                comment_content = comment["content"]
                                comment_content = comment_content.strip()
                                comments_storage.append(comment_content)
                                scores_storage.append(comment["score"])
                                useful_vote_storage.append(comment["usefulVoteCount"])
                                useless_vote_storage.append(comment["uselessVoteCount"])
                                reply_count_storage.append(comment["replyCount"])
                                if "imageCount" in comment:
                                    image_count_storage.append(comment["imageCount"])
                                else:
                                    image_count_storage.append(0)
                                user_level_storage.append(comment["userLevelId"])
                        except Exception, e:
                            print e
                    time.sleep(random.randint(5, 10) / 10.0)
            df = pd.DataFrame({
                "cmt": comments_storage,
                "score": scores_storage,
                "useful_vote": useful_vote_storage,
                "useless_vote": useless_vote_storage,
                "reply": reply_count_storage,
                "image": image_count_storage,
                "level": user_level_storage,
                "id": ids,
                "item_id": father_ids
            })
            df.to_csv('jd.csv', mode="a", index=False, encoding='utf-8', header=False)
            print "%s crawler item%d end" % (self.crawler_name, self.start_index)
            self.start_index += 1


if __name__ == "__main__":
    item_ids = ['642387', '2809096', '694207', '1759611705', '310615', '1568781690', '1217412171', '799558',
                '1276447665', '245544', '1294668504', '16035966', '10605727249', '152173', '10114485603', '1026579',
                '1474246938', '1142292720', '2330905', '1805028', '2963951', '1153536', '10280294050', '1579227994',
                '412632', '1717747487', '1195551', '779158', '1503658981', '1003906446', '1285311', '1205448',
                '1139791', '923933', '1964254', '3334298', '968790', '194814', '574565', '2814961', '4101876',
                '4005186', '10797883769', '492788', '3411568', '1783889194', '607670', '796202', '1023145506',
                '1235209997', '280193', '3266548', '10422926048', '10911819078', '1696679568', '2819304', '1779974720',
                '1496345635', '1271960285', '1550876', '249069', '1699902377', '199613', '10162285819', '743646',
                '1347122', '1788951219', '1671832015', '1217649', '1250535', '1042572581', '1204062751', '2202076',
                '1091934243', '4285130', '1031418', '1151842', '1014158275', '809857', '1011434381', '1176948935',
                '1051310339', '10529925019', '2196506', '697296', '10443781608', '2210057', '962547', '1559666',
                '11038819142', '723468', '623141', '1287322', '1693151474', '1082976838', '1192469', '657984',
                '1409381508', '1015177322', '1031738683', '602697', '1599753', '582599', '1186697', '1091768796',
                '614833', '1107116', '1278560', '1334233593', '1517050272', '1002126', '10324135613', '611665',
                '1160305', '1945374', '1569778', '2201586', '1312367', '162037', '747468', '1226535', '11199156768',
                '1529343230', '819129', '1527421134', '1491791617', '1321313', '1337470', '1416360924', '765578',
                '1005781979', '1388308', '1130155939', '885611', '10984207949', '1148236', '270233', '1018495041',
                '1758559253', '108468', '3812498', '1658981', '3646833', '1029167951', '1276427', '1535834873',
                '257488', '810314', '1478456030', '850165', '305118', '10421570161', '1716586428', '492036', '1345186',
                '1012952', '1128963413', '1765078', '10624109326', '3472476', '2372906', '1285756', '1089309305',
                '1553457306', '1156929485', '1241482261', '1013727158', '206830', '212328', '2102453', '1119071335',
                '1703031', '317534', '1738503807', '2906679', '897630', '841485', '19637836', '10347522739',
                '1215555707', '157381', '1380294562', '1446679844', '213972', '2857565', '867953', '1117367369',
                '3567823', '10529960894', '10314962903', '3053060', '1080885386', '1000054804', '1073608853',
                '1114185', '1625772845', '1046005036', '4227524', '206748', '2744107', '1540428', '110457', '3355543',
                '1135468241', '3639112', '1351487', '4145226', '10368558281', '1025732647', '823030', '2351497',
                '702554', '2677703', '2210013', '1397245399', '1022684941', '1355482807', '1015774', '10807573052',
                '2398623', '10872980463', '1513670220', '2296852', '2299450', '1594790875', '1005961716', '1039928441',
                '1125105384', '1162668325', '1456048560', '11301928198', '1030904648', '1858815', '1513848882',
                '646214', '10282337615', '2142745', '1315752', '101114', '2914921', '1065007018', '1002539253',
                '2955805', '10377270282', '1474535260', '821656', '1108670', '961679', '10362616273', '1424711',
                '1513555', '695063', '1190631508', '617776', '4335506', '1080891917', '1971949', '2425676',
                '1609729174', '1186114446', '1197052', '711778', '1771153526', '10714485924', '576289', '11280177852',
                '1020240717', '1174577', '1068397', '389929', '2901279', '3793032', '2195830', '720003', '1327460543',
                '850129', '1001957796', '1053475182', '10918897552', '10503135341', '269530', '1035831117', '2283382',
                '3929424', '10855147689', '1256848522', '19479614', '1183562', '1124307', '1689701026', '1052996349',
                '1502940', '1342605448', '1649847', '1169056', '1698063706', '1641692125', '10662835349', '2768441',
                '2644083', '1813570', '385902', '3599519', '1041069099', '686943', '1030656', '646197', '1194228',
                '125288', '1094915022', '587167', '896813', '11095584045', '1529552916', '10239438485', '1341907',
                '1445898972', '1350070', '1085723729', '152162', '10048823931', '11135618006', '962979', '1394234351',
                '1011340791', '2341892', '1592764', '1645894014', '1013654097', '10681658867', '236078', '967313',
                '1212521', '1225729493', '1434690501', '726850', '680343', '2463020', '2600812', '1588190265',
                '1371939298', '1789640063', '2322779', '3659541', '117835', '10084755827', '1623076315', '1261486184',
                '775682', '1020423', '1015862676', '1021828373', '3717850', '1131770', '2763759', '346723',
                '1000023352', '1391390263', '1608934474', '1153821194', '1000125', '1176775973', '1381589418', '846117',
                '833614', '876538', '1170541', '1336018', '2243939', '10376848388', '913223', '1335822', '1596677',
                '1658812308', '385642', '1585524588', '1189556798', '1098361', '2640029', '3822827', '1210308489',
                '173701', '757955', '1025083973', '3831894', '1317340', '2486284', '1230194875', '1847498', '16046557',
                '1241331249', '1326496011', '10464602855', '218601', '3713001', '1427144783', '851301', '255741',
                '3153171', '1000895026', '1262662420', '1064223', '1026343457', '1964052', '1946819', '1543523107',
                '1298740', '1724641867', '1198436213', '2868104', '1512469485', '530877', '174419', '959960', '2384078',
                '1455710841', '2138303', '2571617', '1896697', '1219964', '1468444', '11233973117', '1119382',
                '1434284052', '874203', '3522831', '1696779176', '1122862384', '3061636', '362161', '2013641',
                '1223215461', '1006253967', '1340550187', '1135611', '1070186', '1335667252', '1136187269',
                '1518620152', '1308999381', '1094085', '10073955350', '2689308', '1629749837', '831506', '1333583',
                '1032872605', '981285', '1332057', '1929599', '198154', '1238772723', '1081969234', '1523682',
                '3042395', '1308693', '1584522056', '10389958658', '1322463618', '1480157986', '1456833747',
                '11221339751', '1516114070', '812696', '2219600', '315526', '1367958443', '1698961323', '10119874640',
                '3514673', '10386600006', '1031735923', '1041419149', '1026936586', '178025', '10446330011', '663330',
                '203392', '3449652', '1000288028', '1099723', '1364525', '1011084164', '666363', '10426311098',
                '10223955164', '907695', '1228820873', '2145493', '1141138', '513295', '801392', '1020160342', '114095',
                '1534902158', '1282267497', '1033402716', '1018326906', '1591902', '1443446393', '145241', '1128124441',
                '1615556278', '1111428448', '10075884337', '2683224', '19121260', '807509', '1026002', '1607258',
                '1017663587', '1014004678', '1230760', '3251714', '3358895', '657542', '522676', '1125065',
                '10402886630', '1002420069', '1681704563', '3093074', '10123094747', '10477350242', '1516100284',
                '11038421411', '1391314085', '320603', '1243788', '1137310', '611308', '3888518', '1577759040',
                '1165101421', '1564242', '163470', '2141153', '1333333640', '1068098769', '1154661549', '2289438',
                '1137304', '2330242', '1154863426', '1013932631', '10663208490', '1616232565', '3393144', '1002324786',
                '1577513', '136434', '2390704', '1234702237', '920053', '1287329', '1574266825', '1277633',
                '1674562949', '1251042', '1013291978', '1593256', '642947', '1013774863', '2357394', '1859979',
                '771351', '1042718752', '263596', '10361944733', '207772', '1951797214', '10376827198', '1004542',
                '1281380', '1197944785', '10980728147', '1700219737', '1019845570', '1288832207', '964295',
                '1622508260', '1015694800', '1306086234', '1130236939', '1059595415', '1252559385', '1053452045',
                '1885712', '1119366', '1398882710', '1340858', '1265377', '102215', '628453', '1067678451',
                '10100624823', '213177', '644675', '1683864251', '1084054', '262707', '2334545', '319826', '1584815718',
                '1031637802', '1778186388', '957886', '10791192972', '879777', '1552979', '1097992689', '10420446296',
                '3667685', '1658509744', '2949157', '940823', '1034333257', '639236', '854240', '1297858', '1257021707',
                '1516116600', '10530019039', '751624', '10481485249', '4007944', '3668211', '1102514', '1307677',
                '310610', '1811368', '2333570', '1620924', '1708012', '1142167', '202518', '3755947', '1472697704',
                '1677270254', '1409818270', '1074307519', '1106954', '10360382170', '1071221234', '1070209', '914646',
                '698659', '1090268342', '1222850854', '1018561705', '1295040', '10031332548', '2272883', '3798424',
                '840392', '10052308101', '852588', '2165701', '10024610530', '676676', '1774417', '1130085884',
                '312606', '1015399225', '1023220656', '1680589', '968784', '1733115', '3016367', '1015177282', '560592',
                '3322946', '1001349824', '1391495811', '209876', '3078514', '10376826970', '1237667726', '1726270',
                '1315199827', '1568762092', '1010509271', '2218483', '1659329708', '1372514455', '1000164476',
                '1090380', '1027148838', '10037741170', '1038547697', '1416212', '1438982214', '1332772616', '320986',
                '19000468', '10213113023', '517482', '389582', '1276078', '3677824', '1339249862', '231660',
                '1112879526', '16075635', '682002', '1912362', '1287079334', '627181', '1018570059', '10910353765',
                '1150552', '1441722060', '1186229', '1007794745', '1482185802', '10215237522', '1800748211',
                '1361144567', '1263333687', '1181339941', '1397035174', '207560', '1130296', '1007525468', '1083150623',
                '1025219713', '2770346', '279191', '1885691', '1364523', '1005928677', '219492', '1466154214',
                '1820449', '528133', '1535441671', '2611583', '3472877', '10106274649', '964673', '1504105',
                '10194404599', '383439', '2929839', '1134480049', '1250590458', '1130687', '131585', '1647946',
                '1041335544', '1050358177', '1112875', '2334285', '10537416124', '1345200', '1002690931', '840002',
                '1145888221', '2725849', '1531089464', '1097255418', '1555148608', '1561858433', '686874', '1633617818',
                '19148563', '1337797529', '1534382043', '1003770454', '372811', '10345592823', '126744', '1727203',
                '10042952344', '4288966', '708099', '1026815764', '376117', '134733', '2506224', '2089982', '907710',
                '196567', '1383684811', '490543', '19768599', '1153198', '425887', '840000', '1461651364', '2326614',
                '1693897258', '1316327604', '1330619', '2148021', '598376', '10104171008', '1407924258', '1719485390',
                '1273525401', '1318476', '1131569898', '1332660547', '2927460', '1636769', '1146474', '2920563',
                '3675765', '10192168841', '1005796304', '1107849', '1259789', '804322', '1237404890', '1778195',
                '10236551099', '1314731', '695466', '505508', '1288878673', '1282990165', '416905', '1374774224',
                '1055889451', '1800752862', '1383251519', '1751015020', '10257350734', '1333098553', '10122897113',
                '1816103816', '1034315061', '1078466653', '2177980', '900692', '1105064', '1031805313', '1656657586',
                '1003256960', '1670099', '1010693', '867706', '1338282', '1284252341', '231415', '656998', '3093390',
                '232392', '1151292003', '208696', '196961', '10605576194', '1472102', '1032055003', '840172', '728001',
                '1678033647', '10220728807', '1040435709', '1004054966', '1339334737', '1489729', '1568935003',
                '1287334', '10230318181', '744900', '1298348', '3743770', '4135432', '603835', '1185913', '163277',
                '1016355', '125842', '169484', '703303', '1036102386', '1012714937', '1625229383', '1409154374',
                '1463052522', '3035283', '1035902', '1305780226', '1220482158', '1921836', '109881', '1716273506',
                '16076420', '2361715', '2963432', '1012520', '1205729', '2763621', '668571', '1215520', '610586',
                '1003733000', '1368670980', '2342146', '1567979045', '1573900', '1721673455', '1077026', '1337852311',
                '954749', '848852', '879183', '1079587', '2382542', '136485', '10582367805', '1704676077', '3886046',
                '10204133119', '10296311984', '1007479983', '410289', '3453056', '1008391488', '1183185738',
                '1749193830', '1034330292', '1622305096', '1448681741', '1030313987', '1007896805', '1465255127',
                '590092', '728636', '1638835313', '1307668', '522365', '1183796', '2469776', '1069163837', '1340261',
                '1929182', '1045878315', '160512', '1299741', '11299592642', '1588977', '813728', '206942', '1300263',
                '188640', '1358165942', '10737360122', '423478', '730614', '1206032792', '10254020587', '1070355',
                '274576', '1093647153', '1178879', '1037029', '1284002173', '2666369', '1943566', '779900', '158894',
                '1295705', '1584441815', '546871', '720557', '831358', '1297327', '601345', '1488950108', '2338531',
                '1005637315', '1619385700', '4024786', '249037', '1077876', '1108149237', '626081', '1035767659',
                '619640', '3296817', '112566', '797495', '406013', '2198361', '1628476804', '1014840674', '1633613356',
                '1728959', '10619076279', '1038560179', '1022795175', '1285779', '1669767924', '1186710', '1007513544',
                '1456681061', '2538536', '3448188', '2116779', '1242399069', '1017854583', '1806930429', '1335925',
                '1270371', '1892224', '569092', '1317770110', '1502568642', '3717632', '560885', '552478', '1183888',
                '10661794499', '1107902691', '1300255', '3574151', '2787971', '189655', '11288038172', '10377787743',
                '933704', '1026682083', '1335080', '1485130045', '385860', '259687', '1044060', '1169940',
                '10802892904', '1039816', '1613000', '1711976252', '10923204943', '1729708', '1030582', '1624172516',
                '2852404', '1015558695', '1516754041', '237922', '3656571', '1465399133', '10358267887', '123090',
                '1053390919', '1238455', '1580893851', '915884', '10212467407', '1106863950', '1591119', '3146647',
                '4196492', '1350471191', '1589315360', '1010644259', '644486', '1773639', '3506353', '11331701490',
                '1016816323', '1238667982', '788798', '518779', '1421176017', '1221501', '710648', '1311928',
                '10063757236', '1168512', '3496139', '1165212405', '4052970', '683128', '941456', '10464178642',
                '3699785', '996967', '1733089', '661406', '1625783736', '269505', '1030422', '2495712', '965714',
                '963264', '1696739174', '1189537273', '231904', '10740425968', '1032316189', '3274923', '3241147']

    scores = [1, 2, 3]
    crawler1 = JDCrawler(item_ids[0:200], scores, 29, "jd1")
    crawler2 = JDCrawler(item_ids[200:400], scores, 175, "jd2")
    crawler3 = JDCrawler(item_ids[400:600], scores, 197, "jd3")
    crawler4 = JDCrawler(item_ids[600:800], scores, 0, "jd4")
    crawler5 = JDCrawler(item_ids[800:1095], scores, 0, "jd5")
    crawler1.start()
    crawler2.start()
    crawler3.start()
    crawler4.start()
    crawler5.start()
