//新增 或编辑场景
    function addOrEditScence(state,id){
        let appName = null;
        let scenceName = null;
        let scenceState = null;
        let scenceLevel = null;
        let scenceDescribe = null;
        let stepNo = null;
        let caseSeq = null;
        let scenceId = null;
        //0 新增场景 1 编辑场景
        if(state == '0' || state == '1'){
            appName = document.getElementById('appName').value;
            scenceName = document.getElementById('scenceName').value;
            scenceState = document.getElementById('scenceState').value;
            scenceLevel = document.getElementById('scenceLevel').value;
            scenceDescribe = document.getElementById('scenceDescribe').value;
            stepNo = null;
            caseSeq = null;
            scenceId = null;
            if(state == '1'){
                scenceId = id;
            }
        }
        // 3 编辑场景用例
        else if(state == '2'){
            appName = document.getElementById('appName').value;
            scenceId = id;
            caseSeq = caseSeq_ls.toString();
            stepNo = caseSeq_length;
        }
        axios.post('http://'+host+'/addOrEditSceInfo',{
            state:state,
            scenceId:scenceId,
            appName:appName,
            scenceName:scenceName,
            scenceState:scenceState,
            scenceLevel:scenceLevel,
            scenceDescribe:scenceDescribe,
            stepNo:stepNo,
            caseSeq:caseSeq
        }).then(res=>{
            if(res.data.code == '1'){
                alert(res.data.msg);
                closeBox();
                location.href = 'http://'+host+'/scence?appName='+appName;
            }else if(res.data.code != '1'){
                alert(res.data.msg);
            }
            })
    }

        function scenceList(){
        let dataBody = document.getElementById('dataBody');
        dataBody.innerHTML = '';
        let appName = document.getElementById('appName').value;
        let scenceId = document.getElementById('scenceId').value;
        let item;
        let targetItem = ['scence_id','scence_name','scence_level','scence_state','scence_describe'];
        axios.post('http://'+host+'/scenceList',{
            appName:appName,
            scenceId:scenceId,
            pageIndex:pageIndex_init,
            pageSize:pageSize_init
        }).then(res=>{
            let scences = res.data.data;
            let paging_number = res.data.total;
            paging_method(paging_number);
            if(scences.length>0){
                scences.map(scence =>{
                let tr = document.createElement('tr');
                tr.setAttribute('height','40px');
                targetItem.map(target => {
                    //生成所需字段列
                    for(item in scence) {
                        if (target == item) {
                            let td = document.createElement('td');
                            td.setAttribute('title',scence[item]);
                            if(item == 'scence_level' || item == 'scence_state'){
                                td.innerHTML = handleEnum(item,scence[item]);
                            }
                            else if(item == 'scence_describe'){
                                if(!scence[item]){
                                    td.innerHTML = '-';
                                }
                                else{
                                    td.innerHTML = scence[item];
                                }
                            }
                            else{
                                td.innerHTML = scence[item];
                            }
                            tr.appendChild(td);
                        }
                    }
                })
                //操作
                let handleTd = document.createElement('td');
                //运行
                let runBt = document.createElement('button');
                runBt.innerHTML = '运行';
                //展示场景用例运行结果
                runBt.setAttribute('onclick','scenceRunResult('+JSON.stringify(scence)+')')
                handleTd.appendChild(runBt)

                //编辑基本信息
                let editBaseBt = document.createElement('button');
                editBaseBt.innerHTML = '场景编辑';
                editBaseBt.addEventListener('click',function () {
                    popBox('1',scence['scence_id'])
                });
                handleTd.appendChild(editBaseBt)

                //编辑场景用例信息
                let editCaseA = document.createElement('a');
                let editCaseBt = document.createElement('button');
                editCaseA.href = 'http://'+host+'/scenceCase?scenceId='+scence['scence_id'];
                editCaseBt.innerHTML = '用例编辑';
                editCaseA.appendChild(editCaseBt)
                handleTd.appendChild(editCaseA)

                //删除
                let deleteBt = document.createElement('button');
                deleteBt.innerHTML = '删除';
                handleTd.appendChild(deleteBt)
                //onclick事件 删除
                deleteBt.setAttribute('onClick',"deleteSce("+scence['scence_id']+")");
                tr.appendChild(handleTd)
                dataBody.append(tr);
                })
            }
            else if(scences.length==0){
                let tr = document.createElement('tr');
                let td = document.createElement('td');
                td.setAttribute('colspan','6');
                td.innerText = '暂无数据';
                tr.appendChild(td);
                dataBody.appendChild(tr);
            }
        })
    }

    //2022.07.20场景运行展示
    let scenceDialog = document.getElementById('scenceDialog');
    function scenceRunResult(scence=null,caseIdList=null){
        console.log(scence);
        console.log(typeof scence);
        console.log(scence['scence_id']);
        let scenceId_value = null;
        //展示弹窗
        scenceDialog.showModal();
        //先loading
        let scenceLoading = document.getElementById('scenceLoading');
        scenceLoading.style.display = 'block';


        let scenceId = document.getElementById('scenceId_span');
        let scenceName = document.getElementById('scenceName_span');
        let runResult = document.getElementById('runResult');
        let stepNo = document.getElementById('stepNo_span');
        let successNo = document.getElementById('successNo_span');
        let failNo = document.getElementById('failNo_span');
        let successRadio = document.getElementById('successRadio');
        if(scence != null){
            scenceId.innerText = scence['scence_id'];
            scenceName.innerText = scence['scence_name'];
            scenceName.title = scence['scence_name'];
            stepNo.innerText = scence['step_no'];
            scenceId_value = scence['scence_id'];
        }else{
            scenceId.innerText = '-';
            scenceName.innerText = '-';
            stepNo.innerText = '-';
        }
        //生成场景用例运行结果展示elem
        axios.post('http://'+host+'/runSceneTest',{
            scenceId:scenceId_value,
            caseIdList:caseIdList
        }).then(res=> {
            if (res.data) {
                if(res.data.code == 1){
                    scenceLoading.style.display = 'none';

                    let success_number = 0;
                    let fail_number = 0;
                    let success_radio = 0;
                    let case_number = 1;
                    let title_ls = ['实际响应', '预期响应', '请求参数'];
                    let caseResultList = res.data.data;
                    let scenceCasesInfo = document.getElementById('scenceCasesInfo');
                    caseResultList.map(caseResult=>{
                        //用例基本信息
                        let caseInfo_div = document.createElement('div');
                        let caseBasic_div = document.createElement('div');
                        let caseNo_div = document.createElement('div');
                        let caseSeq_div = document.createElement('div');
                        let caseReqType_div = document.createElement('div');
                        let caseRemark_div = document.createElement('div');
                        let caseUrl_div = document.createElement('div');
                        let caseCode_div = document.createElement('div');
                        let caseResult_div = document.createElement('div');
                        let caseFlod_div = document.createElement('div');
                        caseInfo_div.className = 'caseInfo';
                        //生成唯一id
                        caseInfo_div.id = 'caseInfo'+caseResult['caseId'];
                        caseInfo_div.showFlag = false;

                        caseBasic_div.className = 'caseBasic';
                        caseNo_div.className = 'caseNo';
                        caseSeq_div.className = 'caseSeq';
                        caseReqType_div.className = 'caseReqType';
                        caseRemark_div.className = 'caseRemark';
                        caseUrl_div.className = 'caseUrl';
                        caseCode_div.className = 'caseCode';
                        caseResult_div.className = 'caseResult';
                        caseFlod_div.className = 'caseFlod';

                        caseNo_div.innerHTML = case_number;
                        caseSeq_div.innerHTML = caseResult['caseId'];
                        caseReqType_div.innerHTML = caseResult['requestType'];
                        caseRemark_div.innerHTML = (caseResult['remark'] == '' || caseResult['remark'] == null) ? '-' : caseResult['remark'];
                        caseRemark_div.title = caseResult['remark'];
                        caseUrl_div.innerHTML = caseResult['url'];
                        caseUrl_div.title = caseResult['url'];
                        // response 去除转义
                        let actual_resp_srt = caseResult['actual_response'].replace(/[\\]/g, '');
                        let actual_resp_obj = JSON.parse(actual_resp_srt);
                        caseCode_div.innerHTML = actual_resp_obj['code'];
                        caseResult_div.innerHTML = caseResult['results'];
                        caseResult_div.style.color =  caseResult['results']?'green':'red';
                        success_number = caseResult['results']?success_number+1:success_number;
                        fail_number = !caseResult['results']?fail_number+1:fail_number;
                        caseFlod_div.innerHTML = '展开';
                        caseFlod_div.setAttribute('onclick','showCaseDetail(caseInfo'+caseResult['caseId']+',this)');

                        caseBasic_div.appendChild(caseNo_div);
                        caseBasic_div.appendChild(caseSeq_div);
                        caseBasic_div.appendChild(caseReqType_div);
                        caseBasic_div.appendChild(caseRemark_div);
                        caseBasic_div.appendChild(caseUrl_div);
                        caseBasic_div.appendChild(caseCode_div);
                        caseBasic_div.appendChild(caseResult_div);
                        caseBasic_div.appendChild(caseFlod_div);

                        caseInfo_div.appendChild(caseBasic_div);

                        //用例响应请求参数..
                        let caseDetail_div = document.createElement('div');
                        caseDetail_div.className = 'caseDetail';
                        let table = document.createElement('table');
                        let thead = document.createElement('thead');
                        //表头
                        let thead_th = document.createElement('th');
                        title_ls.map(title=>{
                            let thead_td = document.createElement('td');
                            thead_td.innerHTML = title;
                            thead_th.appendChild(thead_td);
                        })
                        thead.appendChild(thead_th);
                        table.appendChild(thead);
                        //表体
                        let tbody = document.createElement('tbody');
                        let tbody_tr = document.createElement('tr');
                        let actual_resp_td = document.createElement('td');
                        let except_resp_td = document.createElement('td');
                        let param_td = document.createElement('td');

                        let except_resp_srt = caseResult['expect_response'].replace(/[\\]/g, '');
                        let except_resp_obj = JSON.parse(except_resp_srt);
                        let param_obj = caseResult['parameter']

                        actual_resp_td.innerHTML = '<pre>'+JSON.stringify(actual_resp_obj, null,2)+'<pre>';
                        except_resp_td.innerHTML = '<pre>'+JSON.stringify(except_resp_obj, null,2)+'<pre>';
                        param_td.innerHTML = '<pre>'+JSON.stringify(param_obj, null,2)+'<pre>';
                        tbody_tr.appendChild(actual_resp_td);
                        tbody_tr.appendChild(except_resp_td);
                        tbody_tr.appendChild(param_td);
                        tbody.appendChild(tbody_tr);
                        table.appendChild(tbody);
                        caseDetail_div.appendChild(table);

                        caseInfo_div.appendChild(caseDetail_div);
                        scenceCasesInfo.appendChild(caseInfo_div);

                        case_number ++;
                    })
                    successNo.innerText = success_number;
                    failNo.innerText = fail_number;
                    runResult.innerText = success_number == caseResultList.length ? '成功' : '失败';
                    runResult.style.color = success_number == caseResultList.length ? 'green' : 'red';
                    success_radio = (Math.round(success_number / caseResultList.length * 10000) / 100.00);
                    successRadio.innerText = success_radio + '%';
                    showScenceCase();
                }
                else {
                    closeScenceDialog();
                    alert(res.data.msg);
                }
            }
        })
    }

    function showScenceCase(){
        //展示用例
        let scenceBox = document.getElementById('scenceBox');
        scenceBox.style.display = 'block';
        //初始化casesDetail
        let caseDetails = document.getElementsByClassName('caseDetail');
        for(let i = 0;i<caseDetails.length;i++){
            caseDetails[i].style.display = 'none';
        }
    }

    function showCaseDetail(caseInfo,flodElem){
        //所有caseInfo 给一个classname 生成时单独给id，展示交互用id
        let caseDetails = caseInfo.children[1];
        if (!caseInfo.showFlag){
            //展示用例执行详情
            caseInfo.style.height = '400px';
            caseDetails.style.display = 'block';
            caseInfo.showFlag = true;
            flodElem.innerHTML = '收起';
        }
        else{
            //收起
            caseInfo.style.height = '40px';
            caseDetails.style.display = 'none';
            caseInfo.showFlag = false;
            flodElem.innerHTML = '展开';
        }
    }

    function closeScenceDialog(){
        //关闭弹窗
        let scenceCasesInfo = document.getElementById('scenceCasesInfo');
        let scenceBox = document.getElementById('scenceBox');
        scenceCasesInfo.innerHTML = '';
        scenceBox.style.display = 'none';
        scenceDialog.close();
    }