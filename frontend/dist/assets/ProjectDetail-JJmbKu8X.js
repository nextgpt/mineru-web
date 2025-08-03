import{a as H,c as v,b as e,t as w,f as t,r as c,w as o,e as m,u as V,h as K,l as oe,E as f,i as d,_ as W,j as p,o as J,k as U,m as P,N as Z,D as Q,n as se,g as le,Q as _e,G as pe,O as ve,z as me,M as fe,P as ge,A as ye}from"./index-BHN-jLFm.js";import{p as Y}from"./projects-B10Zn0n3.js";import"./user-COjPqb4h.js";const $e={class:"project-info-component"},be={class:"info-section"},we={class:"info-grid"},ke={class:"info-item"},je={class:"info-value"},xe={class:"info-item"},he={class:"info-value"},Ie={class:"info-item"},Ce={class:"info-value"},ze={class:"info-item"},De={class:"info-value"},Se={class:"info-item full-width"},Ve={class:"info-value"},qe={key:0,class:"info-section"},Me={class:"file-info-card"},Te={class:"file-icon"},Pe={class:"file-details"},Be={class:"file-name"},Fe={class:"file-meta"},Oe={class:"file-size"},Ae={class:"file-status"},Re={class:"file-actions"},Ue={key:1,class:"info-section"},Ee={class:"empty-state"},Le=H({__name:"ProjectInfo",props:{project:{}},emits:["refresh"],setup(B){const C=n=>({created:"info",parsing:"warning",analyzing:"warning",outline_generated:"primary",document_generating:"primary",completed:"success",failed:"danger"})[n]||"info",u=n=>({created:"已创建",parsing:"解析中",analyzing:"分析中",outline_generated:"大纲已生成",document_generating:"生成中",completed:"已完成",failed:"失败"})[n]||n,a=n=>new Date(n).toLocaleString("zh-CN"),j=n=>{if(n===0)return"0 B";const s=1024,x=["B","KB","MB","GB"],$=Math.floor(Math.log(n)/Math.log(s));return parseFloat((n/Math.pow(s,$)).toFixed(2))+" "+x[$]},z=()=>{f.info("下载功能开发中...")},y=()=>{f.info("预览功能开发中...")};return(n,s)=>{const x=c("el-tag"),$=c("el-icon"),g=c("el-button");return d(),v("div",$e,[e("div",be,[s[5]||(s[5]=e("h3",{class:"section-title"},"项目基本信息",-1)),e("div",we,[e("div",ke,[s[0]||(s[0]=e("label",{class:"info-label"},"项目名称",-1)),e("div",je,w(n.project.name),1)]),e("div",xe,[s[1]||(s[1]=e("label",{class:"info-label"},"项目状态",-1)),e("div",he,[t(x,{type:C(n.project.status),size:"small"},{default:o(()=>[m(w(u(n.project.status)),1)]),_:1},8,["type"])])]),e("div",Ie,[s[2]||(s[2]=e("label",{class:"info-label"},"创建时间",-1)),e("div",Ce,w(a(n.project.created_at)),1)]),e("div",ze,[s[3]||(s[3]=e("label",{class:"info-label"},"最后更新",-1)),e("div",De,w(a(n.project.updated_at)),1)]),e("div",Se,[s[4]||(s[4]=e("label",{class:"info-label"},"项目描述",-1)),e("div",Ve,w(n.project.description||"暂无描述"),1)])])]),n.project.original_file?(d(),v("div",qe,[s[8]||(s[8]=e("h3",{class:"section-title"},"招标文件信息",-1)),e("div",Me,[e("div",Te,[t($,{size:"32"},{default:o(()=>[t(V(K))]),_:1})]),e("div",Pe,[e("div",Be,w(n.project.original_file.filename),1),e("div",Fe,[e("span",Oe,w(j(n.project.original_file.size)),1),e("span",Ae,w(n.project.original_file.status),1)])]),e("div",Re,[t(g,{size:"small",onClick:z},{default:o(()=>s[6]||(s[6]=[m("下载")])),_:1,__:[6]}),t(g,{size:"small",type:"primary",onClick:y},{default:o(()=>s[7]||(s[7]=[m("预览")])),_:1,__:[7]})])])])):(d(),v("div",Ue,[s[11]||(s[11]=e("h3",{class:"section-title"},"招标文件",-1)),e("div",Ee,[t($,{size:"48",color:"#d1d5db"},{default:o(()=>[t(V(oe))]),_:1}),s[9]||(s[9]=e("p",{class:"empty-text"},"尚未上传招标文件",-1)),s[10]||(s[10]=e("p",{class:"empty-hint"},"请先上传招标文件以开始项目分析",-1))])]))])}}}),Ne=W(Le,[["__scopeId","data-v-46559262"]]),He={class:"requirement-analysis-component"},We={class:"analysis-header"},Ge={key:0,class:"analyzing-state"},Qe={class:"analyzing-content"},Ke={key:1,class:"analysis-results"},Je={class:"results-grid"},Xe={class:"result-card"},Ye={class:"card-content"},Ze={class:"content-text"},et={class:"result-card"},tt={class:"card-content"},st={class:"content-text"},ot={class:"result-card"},lt={class:"card-content"},nt={class:"content-text"},at={class:"result-card full-width"},it={class:"card-content"},rt={class:"content-text"},dt={class:"requirements-classification"},ut={class:"requirement-content"},ct=["innerHTML"],_t={key:1,class:"empty-requirement"},pt={class:"requirement-content"},vt=["innerHTML"],mt={key:1,class:"empty-requirement"},ft={class:"requirement-content"},gt=["innerHTML"],yt={key:1,class:"empty-requirement"},$t={key:2,class:"empty-state"},bt=H({__name:"RequirementAnalysis",props:{projectId:{}},setup(B){const C=B,u=p(null),a=p(!1),j=p("critical"),z=async()=>{try{a.value=!0,f.info("开始分析招标文件，请稍候..."),setTimeout(()=>{a.value=!1,f.success("需求分析完成"),y()},3e3)}catch(n){console.error("开始分析失败:",n),f.error("开始分析失败"),a.value=!1}},y=async()=>{try{u.value={id:1,project_id:C.projectId,user_id:"user123",project_overview:"这是一个关于智能办公系统建设的招标项目，旨在提升办公效率和数字化水平。",client_info:"招标单位：某市政府办公厅，联系人：张主任，预算范围：100-200万元。",budget_info:"项目总预算约150万元，包含软件开发、硬件采购、实施部署等费用。",detailed_requirements:"系统需要包含文档管理、流程审批、视频会议、即时通讯等核心功能模块。",critical_requirements:"<ul><li>系统稳定性要求99.9%以上</li><li>支持1000+并发用户</li><li>数据安全等级要求三级</li></ul>",important_requirements:"<ul><li>界面友好易用</li><li>移动端适配</li><li>与现有系统集成</li></ul>",general_requirements:"<ul><li>提供用户培训</li><li>一年免费维护</li><li>技术文档完整</li></ul>",created_at:new Date().toISOString()}}catch(n){console.error("加载分析结果失败:",n)}};return J(()=>{y()}),(n,s)=>{const x=c("el-button"),$=c("el-icon"),g=c("el-tab-pane"),M=c("el-tabs");return d(),v("div",He,[e("div",We,[s[2]||(s[2]=e("h3",{class:"section-title"},"需求分析",-1)),!u.value&&!a.value?(d(),U(x,{key:0,type:"primary",onClick:z},{default:o(()=>s[1]||(s[1]=[m(" 开始分析 ")])),_:1,__:[1]})):P("",!0)]),a.value?(d(),v("div",Ge,[e("div",Qe,[t($,{class:"analyzing-icon",size:"48"},{default:o(()=>[t(V(Z))]),_:1}),s[3]||(s[3]=e("h4",{class:"analyzing-title"},"正在分析招标文件...",-1)),s[4]||(s[4]=e("p",{class:"analyzing-text"},"AI正在深度分析招标文件内容，提取关键需求信息，请稍候。",-1))])])):u.value?(d(),v("div",Ke,[e("div",Je,[e("div",Xe,[s[5]||(s[5]=e("div",{class:"card-header"},[e("h4",{class:"card-title"},"项目概览")],-1)),e("div",Ye,[e("p",Ze,w(u.value.project_overview||"暂无数据"),1)])]),e("div",et,[s[6]||(s[6]=e("div",{class:"card-header"},[e("h4",{class:"card-title"},"甲方信息")],-1)),e("div",tt,[e("p",st,w(u.value.client_info||"暂无数据"),1)])]),e("div",ot,[s[7]||(s[7]=e("div",{class:"card-header"},[e("h4",{class:"card-title"},"预算信息")],-1)),e("div",lt,[e("p",nt,w(u.value.budget_info||"暂无数据"),1)])]),e("div",at,[s[8]||(s[8]=e("div",{class:"card-header"},[e("h4",{class:"card-title"},"详细需求")],-1)),e("div",it,[e("p",rt,w(u.value.detailed_requirements||"暂无数据"),1)])])]),e("div",dt,[s[9]||(s[9]=e("h4",{class:"classification-title"},"需求分级",-1)),t(M,{modelValue:j.value,"onUpdate:modelValue":s[0]||(s[0]=F=>j.value=F),class:"requirement-tabs"},{default:o(()=>[t(g,{label:"关键需求",name:"critical"},{default:o(()=>[e("div",ut,[u.value.critical_requirements?(d(),v("div",{key:0,innerHTML:u.value.critical_requirements},null,8,ct)):(d(),v("p",_t,"暂无关键需求数据"))])]),_:1}),t(g,{label:"重要需求",name:"important"},{default:o(()=>[e("div",pt,[u.value.important_requirements?(d(),v("div",{key:0,innerHTML:u.value.important_requirements},null,8,vt)):(d(),v("p",mt,"暂无重要需求数据"))])]),_:1}),t(g,{label:"一般需求",name:"general"},{default:o(()=>[e("div",ft,[u.value.general_requirements?(d(),v("div",{key:0,innerHTML:u.value.general_requirements},null,8,gt)):(d(),v("p",yt,"暂无一般需求数据"))])]),_:1})]),_:1},8,["modelValue"])])])):(d(),v("div",$t,[t($,{size:"48",color:"#d1d5db"},{default:o(()=>[t(V(K))]),_:1}),s[10]||(s[10]=e("h4",{class:"empty-title"},"尚未进行需求分析",-1)),s[11]||(s[11]=e("p",{class:"empty-text"},'点击"开始分析"按钮，AI将自动分析招标文件并提取关键需求信息。',-1))]))])}}}),wt=W(bt,[["__scopeId","data-v-ea3a5ab6"]]),kt={class:"bid-outline-component"},jt={class:"outline-header"},xt={key:0,class:"generating-state"},ht={class:"generating-content"},It={key:1,class:"outline-tree"},Ct={class:"outline-node"},zt={class:"node-content"},Dt={class:"node-sequence"},St={class:"node-title"},Vt={key:0,class:"node-description"},qt={class:"node-actions"},Mt={key:2,class:"empty-state"},Tt={class:"dialog-footer"},Pt=H({__name:"BidOutline",props:{projectId:{}},setup(B){const C=B,u=p([]),a=p(!1),j=p(!1),z=p(),y=p(null),n=p({title:"",content:""}),s={title:[{required:!0,message:"请输入大纲标题",trigger:"blur"},{min:1,max:200,message:"标题长度在 1 到 200 个字符",trigger:"blur"}]},x=Q(()=>{const b=(i,h)=>i.filter(D=>D.parent_id===h).sort((D,O)=>D.order_index-O.order_index).map(D=>({...D,children:b(i,D.id)}));return b(u.value)}),$=async()=>{try{a.value=!0,f.info("开始生成标书大纲，请稍候..."),setTimeout(()=>{a.value=!1,f.success("标书大纲生成完成"),g()},3e3)}catch(b){console.error("生成大纲失败:",b),f.error("生成大纲失败"),a.value=!1}},g=async()=>{try{u.value=[{id:1,project_id:C.projectId,user_id:"user123",title:"项目概述",level:1,sequence:"1",order_index:1,content:"项目背景、目标和范围说明",created_at:new Date().toISOString()},{id:2,project_id:C.projectId,user_id:"user123",title:"项目背景",level:2,sequence:"1.1",parent_id:1,order_index:1,content:"详细描述项目产生的背景和必要性",created_at:new Date().toISOString()},{id:3,project_id:C.projectId,user_id:"user123",title:"项目目标",level:2,sequence:"1.2",parent_id:1,order_index:2,content:"明确项目要达到的具体目标",created_at:new Date().toISOString()},{id:4,project_id:C.projectId,user_id:"user123",title:"技术方案",level:1,sequence:"2",order_index:2,content:"详细的技术实现方案",created_at:new Date().toISOString()},{id:5,project_id:C.projectId,user_id:"user123",title:"系统架构设计",level:2,sequence:"2.1",parent_id:4,order_index:1,content:"系统整体架构和技术选型",created_at:new Date().toISOString()},{id:6,project_id:C.projectId,user_id:"user123",title:"功能模块设计",level:2,sequence:"2.2",parent_id:4,order_index:2,content:"各功能模块的详细设计",created_at:new Date().toISOString()}]}catch(b){console.error("加载大纲失败:",b)}},M=b=>{y.value=b,n.value={title:b.title,content:b.content||""},j.value=!0},F=async()=>{if(!(!z.value||!y.value))try{if(!await z.value.validate())return;const i=u.value.find(h=>h.id===y.value.id);i&&(i.title=n.value.title,i.content=n.value.content),f.success("大纲更新成功"),j.value=!1}catch(b){console.error("更新大纲失败:",b),f.error("更新大纲失败")}},E=b=>{f.info(`正在为"${b.title}"生成内容...`)};return J(()=>{g()}),(b,i)=>{const h=c("el-button"),D=c("el-icon"),O=c("el-tree"),R=c("el-input"),I=c("el-form-item"),l=c("el-form"),S=c("el-dialog");return d(),v("div",kt,[e("div",jt,[i[5]||(i[5]=e("h3",{class:"section-title"},"标书大纲",-1)),!u.value.length&&!a.value?(d(),U(h,{key:0,type:"primary",onClick:$},{default:o(()=>i[4]||(i[4]=[m(" 生成大纲 ")])),_:1,__:[4]})):P("",!0)]),a.value?(d(),v("div",xt,[e("div",ht,[t(D,{class:"generating-icon",size:"48"},{default:o(()=>[t(V(Z))]),_:1}),i[6]||(i[6]=e("h4",{class:"generating-title"},"正在生成标书大纲...",-1)),i[7]||(i[7]=e("p",{class:"generating-text"},"AI正在基于需求分析结果生成结构化的标书大纲，请稍候。",-1))])])):u.value.length?(d(),v("div",It,[t(O,{data:x.value,props:{children:"children",label:"title"},"node-key":"id","default-expand-all":"",class:"outline-tree-component"},{default:o(({data:k})=>[e("div",Ct,[e("div",zt,[e("span",Dt,w(k.sequence),1),e("span",St,w(k.title),1),k.content?(d(),v("span",Vt,w(k.content),1)):P("",!0)]),e("div",qt,[t(h,{size:"small",onClick:se(L=>M(k),["stop"])},{default:o(()=>i[8]||(i[8]=[m(" 编辑 ")])),_:2,__:[8]},1032,["onClick"]),t(h,{size:"small",type:"primary",onClick:se(L=>E(k),["stop"])},{default:o(()=>i[9]||(i[9]=[m(" 生成内容 ")])),_:2,__:[9]},1032,["onClick"])])])]),_:1},8,["data"])])):(d(),v("div",Mt,[t(D,{size:"48",color:"#d1d5db"},{default:o(()=>[t(V(K))]),_:1}),i[10]||(i[10]=e("h4",{class:"empty-title"},"尚未生成标书大纲",-1)),i[11]||(i[11]=e("p",{class:"empty-text"},"基于需求分析结果，AI将为您生成结构化的标书大纲。",-1))])),t(S,{modelValue:j.value,"onUpdate:modelValue":i[3]||(i[3]=k=>j.value=k),title:"编辑大纲项",width:"500px"},{footer:o(()=>[e("span",Tt,[t(h,{onClick:i[2]||(i[2]=k=>j.value=!1)},{default:o(()=>i[12]||(i[12]=[m("取消")])),_:1,__:[12]}),t(h,{type:"primary",onClick:F},{default:o(()=>i[13]||(i[13]=[m(" 保存 ")])),_:1,__:[13]})])]),default:o(()=>[t(l,{ref_key:"editFormRef",ref:z,model:n.value,rules:s,"label-width":"80px"},{default:o(()=>[t(I,{label:"标题",prop:"title"},{default:o(()=>[t(R,{modelValue:n.value.title,"onUpdate:modelValue":i[0]||(i[0]=k=>n.value.title=k),placeholder:"请输入大纲标题",maxlength:"200","show-word-limit":""},null,8,["modelValue"])]),_:1}),t(I,{label:"描述",prop:"content"},{default:o(()=>[t(R,{modelValue:n.value.content,"onUpdate:modelValue":i[1]||(i[1]=k=>n.value.content=k),type:"textarea",rows:3,placeholder:"请输入大纲描述（可选）",maxlength:"500","show-word-limit":""},null,8,["modelValue"])]),_:1})]),_:1},8,["model"])]),_:1},8,["modelValue"])])}}}),Bt=W(Pt,[["__scopeId","data-v-0d6a5c45"]]),Ft={class:"bid-document-component"},Ot={class:"document-header"},At={class:"document-actions"},Rt={key:0,class:"generating-state"},Ut={class:"generating-content"},Et={class:"progress-info"},Lt={class:"progress-text"},Nt={key:1,class:"document-content"},Ht={class:"document-toolbar"},Wt={class:"toolbar-left"},Gt={class:"toolbar-right"},Qt={class:"word-count"},Kt={key:0,class:"document-editor"},Jt={key:1,class:"document-preview"},Xt=["innerHTML"],Yt={key:2,class:"empty-state"},Zt={class:"export-options"},es={class:"dialog-footer"},ts=H({__name:"BidDocument",props:{projectId:{}},setup(B){const C=B,u=p(null),a=p(!1),j=p(!1),z=p(!1),y=p("edit"),n=p(""),s=p(0),x=p(),$=p(""),g=p(!1),M=p("pdf"),F=Q(()=>n.value.replace(/\s/g,"").length),E=Q(()=>n.value.replace(/\n/g,"<br>").replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>").replace(/\*(.*?)\*/g,"<em>$1</em>")),b=async()=>{try{a.value=!0,s.value=0,$.value="正在初始化生成任务...";const I=[{progress:20,text:"正在分析大纲结构..."},{progress:40,text:"正在生成项目概述..."},{progress:60,text:"正在生成技术方案..."},{progress:80,text:"正在生成实施计划..."},{progress:100,text:"标书生成完成！"}];for(const l of I)await new Promise(S=>setTimeout(S,1e3)),s.value=l.progress,$.value=l.text;n.value=`# 智能办公系统建设项目技术方案

## 1. 项目概述

### 1.1 项目背景

随着信息技术的快速发展和数字化转型的深入推进，传统的办公模式已经无法满足现代企业高效、协同、智能化的办公需求。本项目旨在构建一套完整的智能办公系统，通过先进的技术手段提升办公效率，优化工作流程，实现办公环境的数字化升级。

### 1.2 项目目标

本项目的主要目标包括：
- 建设统一的智能办公平台，整合各类办公应用
- 实现办公流程的数字化和自动化
- 提供便捷的移动办公解决方案
- 建立完善的数据安全保障体系
- 提升整体办公效率30%以上

## 2. 技术方案

### 2.1 系统架构设计

本系统采用微服务架构设计，具备高可用、高并发、易扩展的特点。整体架构分为以下几个层次：

**前端展示层**
- Web端：基于Vue.js 3.0框架开发
- 移动端：采用React Native跨平台开发
- 桌面端：使用Electron技术栈

**API网关层**
- 统一的API入口管理
- 请求路由和负载均衡
- 安全认证和权限控制

**业务服务层**
- 用户管理服务
- 文档管理服务
- 流程审批服务
- 即时通讯服务
- 视频会议服务

**数据存储层**
- 关系型数据库：PostgreSQL
- 缓存数据库：Redis
- 文件存储：MinIO对象存储
- 搜索引擎：Elasticsearch

### 2.2 核心功能模块

**文档管理模块**
- 支持多种文档格式的在线预览和编辑
- 版本控制和协同编辑功能
- 智能分类和全文检索
- 文档安全权限管理

**流程审批模块**
- 可视化流程设计器
- 灵活的审批规则配置
- 移动端审批支持
- 审批过程全程跟踪

**即时通讯模块**
- 实时消息推送
- 群组聊天和文件共享
- 消息加密传输
- 离线消息存储

**视频会议模块**
- 高清音视频通话
- 屏幕共享和白板功能
- 会议录制和回放
- 多终端同步接入

## 3. 技术特色

### 3.1 人工智能集成

系统集成了多项AI技术，包括：
- 智能文档分析和摘要生成
- 语音转文字和智能会议纪要
- 智能日程安排和提醒
- 基于机器学习的个性化推荐

### 3.2 安全保障

采用多层次的安全防护措施：
- 数据传输加密（TLS 1.3）
- 数据存储加密（AES-256）
- 多因子身份认证
- 细粒度权限控制
- 安全审计日志

### 3.3 性能优化

通过多种技术手段保障系统性能：
- 分布式缓存策略
- 数据库读写分离
- CDN内容分发
- 异步任务处理
- 智能负载均衡

## 4. 实施计划

### 4.1 项目阶段划分

**第一阶段（1-2个月）：基础平台建设**
- 系统架构搭建
- 基础服务开发
- 数据库设计和部署

**第二阶段（3-4个月）：核心功能开发**
- 文档管理模块开发
- 流程审批模块开发
- 用户权限系统开发

**第三阶段（5-6个月）：高级功能开发**
- 即时通讯模块开发
- 视频会议模块开发
- AI功能集成

**第四阶段（7-8个月）：系统集成和测试**
- 系统集成测试
- 性能优化调试
- 安全测试验证

**第五阶段（9个月）：部署上线**
- 生产环境部署
- 用户培训和支持
- 系统稳定性监控

### 4.2 质量保证

- 建立完善的代码审查机制
- 实施自动化测试流程
- 定期进行安全漏洞扫描
- 建立持续集成和部署流程

## 5. 预期效果

通过本项目的实施，预期将达到以下效果：

- **效率提升**：整体办公效率提升30%以上
- **成本节约**：减少纸质文档使用，降低办公成本20%
- **协同增强**：跨部门协作效率提升50%
- **安全保障**：建立企业级安全防护体系
- **用户体验**：提供统一、便捷的办公体验

## 6. 总结

本技术方案基于先进的技术架构和丰富的行业经验，能够为客户提供一套完整、高效、安全的智能办公解决方案。我们承诺严格按照项目计划执行，确保项目按时、按质完成，为客户创造最大价值。`,u.value={id:1,project_id:C.projectId,user_id:"user123",title:"智能办公系统建设项目技术方案",content:n.value,status:"generated",version:1,created_at:new Date().toISOString(),updated_at:new Date().toISOString()},a.value=!1,f.success("标书生成完成")}catch(I){console.error("生成标书失败:",I),f.error("生成标书失败"),a.value=!1,x.value="exception"}},i=async()=>{},h=()=>{u.value&&u.value.status==="generated"&&(u.value.status="edited")},D=async()=>{if(u.value)try{j.value=!0,u.value.content=n.value,u.value.updated_at=new Date().toISOString(),f.success("文档保存成功")}catch(I){console.error("保存文档失败:",I),f.error("保存文档失败")}finally{j.value=!1}},O=()=>{g.value=!0},R=async()=>{try{z.value=!0,await new Promise(I=>setTimeout(I,2e3)),f.success(`文档已导出为 ${M.value.toUpperCase()} 格式`),g.value=!1}catch(I){console.error("导出文档失败:",I),f.error("导出文档失败")}finally{z.value=!1}};return J(()=>{i()}),(I,l)=>{const S=c("el-button"),k=c("el-icon"),L=c("el-progress"),_=c("el-button-group"),r=c("el-input"),T=c("el-radio"),A=c("el-radio-group"),X=c("el-dialog");return d(),v("div",Ft,[e("div",Ot,[l[8]||(l[8]=e("h3",{class:"section-title"},"标书内容",-1)),e("div",At,[!u.value&&!a.value?(d(),U(S,{key:0,type:"primary",onClick:b},{default:o(()=>l[6]||(l[6]=[m(" 生成完整标书 ")])),_:1,__:[6]})):P("",!0),u.value?(d(),U(S,{key:1,onClick:O},{default:o(()=>[t(k,null,{default:o(()=>[t(V(le))]),_:1}),l[7]||(l[7]=m(" 导出文档 "))]),_:1,__:[7]})):P("",!0)])]),a.value?(d(),v("div",Rt,[e("div",Ut,[t(k,{class:"generating-icon",size:"48"},{default:o(()=>[t(V(Z))]),_:1}),l[9]||(l[9]=e("h4",{class:"generating-title"},"正在生成标书内容...",-1)),l[10]||(l[10]=e("p",{class:"generating-text"},"AI正在基于大纲结构生成完整的标书内容，这可能需要几分钟时间。",-1)),e("div",Et,[t(L,{percentage:s.value,status:x.value},null,8,["percentage","status"]),e("p",Lt,w($.value),1)])])])):u.value?(d(),v("div",Nt,[e("div",Ht,[e("div",Wt,[t(_,null,{default:o(()=>[t(S,{type:y.value==="edit"?"primary":"",onClick:l[0]||(l[0]=q=>y.value="edit"),size:"small"},{default:o(()=>l[11]||(l[11]=[m(" 编辑模式 ")])),_:1,__:[11]},8,["type"]),t(S,{type:y.value==="preview"?"primary":"",onClick:l[1]||(l[1]=q=>y.value="preview"),size:"small"},{default:o(()=>l[12]||(l[12]=[m(" 预览模式 ")])),_:1,__:[12]},8,["type"])]),_:1})]),e("div",Gt,[e("span",Qt,"字数: "+w(F.value),1),t(S,{size:"small",onClick:D,loading:j.value},{default:o(()=>l[13]||(l[13]=[m(" 保存 ")])),_:1,__:[13]},8,["loading"])])]),y.value==="edit"?(d(),v("div",Kt,[t(r,{modelValue:n.value,"onUpdate:modelValue":l[2]||(l[2]=q=>n.value=q),type:"textarea",rows:25,placeholder:"标书内容将在这里显示...",onInput:h,class:"editor-textarea"},null,8,["modelValue"])])):(d(),v("div",Jt,[e("div",{class:"preview-content",innerHTML:E.value},null,8,Xt)]))])):(d(),v("div",Yt,[t(k,{size:"48",color:"#d1d5db"},{default:o(()=>[t(V(K))]),_:1}),l[14]||(l[14]=e("h4",{class:"empty-title"},"尚未生成标书内容",-1)),l[15]||(l[15]=e("p",{class:"empty-text"},"基于标书大纲，AI将为您生成完整的标书内容。",-1))])),t(X,{modelValue:g.value,"onUpdate:modelValue":l[5]||(l[5]=q=>g.value=q),title:"导出标书文档",width:"400px"},{footer:o(()=>[e("span",es,[t(S,{onClick:l[4]||(l[4]=q=>g.value=!1)},{default:o(()=>l[20]||(l[20]=[m("取消")])),_:1,__:[20]}),t(S,{type:"primary",onClick:R,loading:z.value},{default:o(()=>l[21]||(l[21]=[m(" 导出 ")])),_:1,__:[21]},8,["loading"])])]),default:o(()=>[e("div",Zt,[l[19]||(l[19]=e("h4",null,"选择导出格式：",-1)),t(A,{modelValue:M.value,"onUpdate:modelValue":l[3]||(l[3]=q=>M.value=q)},{default:o(()=>[t(T,{label:"pdf"},{default:o(()=>l[16]||(l[16]=[m("PDF 格式")])),_:1,__:[16]}),t(T,{label:"docx"},{default:o(()=>l[17]||(l[17]=[m("Word 格式")])),_:1,__:[17]}),t(T,{label:"md"},{default:o(()=>l[18]||(l[18]=[m("Markdown 格式")])),_:1,__:[18]})]),_:1},8,["modelValue"])])]),_:1},8,["modelValue"])])}}}),ss=W(ts,[["__scopeId","data-v-17045fd5"]]),os={class:"project-detail-page"},ls={class:"page-header"},ns={class:"header-left"},as={class:"project-info"},is={class:"project-title"},rs={class:"project-meta"},ds={key:1,class:"create-time"},us={class:"header-right"},cs={class:"page-content"},_s={key:0,class:"content-container"},ps={class:"tab-content"},vs={class:"tab-content"},ms={class:"tab-content"},fs={class:"tab-content"},gs={class:"upload-content"},ys={key:0,class:"upload-progress"},$s={class:"dialog-footer"},bs=H({__name:"ProjectDetail",setup(B){const C=_e(),u=me(),a=p(null),j=p(!1),z=p("info"),y=p(!1),n=p(),s=p(null),x=p(!1),$=p(0),g=p(),M=Q(()=>{const _=C.params.id;return typeof _=="string"?parseInt(_):0}),F=_=>({created:"info",parsing:"warning",analyzing:"warning",outline_generated:"primary",document_generating:"primary",completed:"success",failed:"danger"})[_]||"info",E=_=>({created:"已创建",parsing:"解析中",analyzing:"分析中",outline_generated:"大纲已生成",document_generating:"生成中",completed:"已完成",failed:"失败"})[_]||_,b=_=>new Date(_).toLocaleString("zh-CN"),i=()=>{u.push("/projects")},h=async()=>{if(!M.value){f.error("项目ID无效"),i();return}try{j.value=!0,a.value=await Y.getProject(M.value)}catch(_){console.error("加载项目详情失败:",_),f.error("加载项目详情失败"),i()}finally{j.value=!1}},D=_=>{switch(_){case"edit":O();break;case"delete":R();break}},O=()=>{f.info("编辑功能开发中...")},R=async()=>{if(a.value)try{await ye.confirm(`确定要删除项目"${a.value.name}"吗？此操作不可恢复。`,"确认删除",{confirmButtonText:"确定",cancelButtonText:"取消",type:"warning"}),await Y.deleteProject(a.value.id),f.success("项目删除成功"),i()}catch(_){_!=="cancel"&&(console.error("删除项目失败:",_),f.error("删除项目失败"))}},I=_=>{_.raw&&(s.value=_.raw)},l=()=>{s.value=null},S=_=>{const r=["application/pdf","application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document"].includes(_.type),T=_.size/1024/1024<100;return r?T?!0:(f.error("文件大小不能超过 100MB"),!1):(f.error("只支持 PDF、Word 格式的文件"),!1)},k=async()=>{if(!(!s.value||!a.value))try{x.value=!0,$.value=0,g.value=void 0,await Y.uploadTenderFile(a.value.id,s.value,_=>{$.value=_}),g.value="success",f.success("文件上传成功"),y.value=!1,await h()}catch(_){console.error("文件上传失败:",_),g.value="exception",f.error("文件上传失败")}finally{x.value=!1}},L=_=>{var r;if(x.value){f.warning("正在上传文件，请稍候...");return}s.value=null,$.value=0,g.value=void 0,(r=n.value)==null||r.clearFiles(),_()};return J(()=>{h()}),(_,r)=>{var ee,te;const T=c("el-icon"),A=c("el-button"),X=c("el-tag"),q=c("el-dropdown-item"),ne=c("el-dropdown-menu"),ae=c("el-dropdown"),G=c("el-tab-pane"),ie=c("el-tabs"),re=c("el-upload"),de=c("el-progress"),ue=c("el-dialog"),ce=ve("loading");return d(),v("div",os,[e("div",ls,[e("div",ns,[t(A,{onClick:i,class:"back-button"},{default:o(()=>[t(T,null,{default:o(()=>[t(V(fe))]),_:1}),r[4]||(r[4]=m(" 返回项目列表 "))]),_:1,__:[4]}),e("div",as,[e("h1",is,w(((ee=a.value)==null?void 0:ee.name)||"加载中..."),1),e("div",rs,[a.value?(d(),U(X,{key:0,type:F(a.value.status),size:"small"},{default:o(()=>[m(w(E(a.value.status)),1)]),_:1},8,["type"])):P("",!0),a.value?(d(),v("span",ds," 创建于 "+w(b(a.value.created_at)),1)):P("",!0)])])]),e("div",us,[(te=a.value)!=null&&te.original_file?P("",!0):(d(),U(A,{key:0,type:"primary",onClick:r[0]||(r[0]=N=>y.value=!0)},{default:o(()=>[t(T,null,{default:o(()=>[t(V(le))]),_:1}),r[5]||(r[5]=m(" 上传招标文件 "))]),_:1,__:[5]})),t(ae,{onCommand:D},{dropdown:o(()=>[t(ne,null,{default:o(()=>[t(q,{command:"edit"},{default:o(()=>r[7]||(r[7]=[m("编辑项目")])),_:1,__:[7]}),t(q,{command:"delete",divided:""},{default:o(()=>r[8]||(r[8]=[m("删除项目")])),_:1,__:[8]})]),_:1})]),default:o(()=>[t(A,null,{default:o(()=>[r[6]||(r[6]=m(" 更多操作 ")),t(T,{class:"el-icon--right"},{default:o(()=>[t(V(ge))]),_:1})]),_:1,__:[6]})]),_:1})])]),pe((d(),v("div",cs,[a.value?(d(),v("div",_s,[t(ie,{modelValue:z.value,"onUpdate:modelValue":r[1]||(r[1]=N=>z.value=N),class:"project-tabs"},{default:o(()=>[t(G,{label:"基本信息",name:"info"},{default:o(()=>[e("div",ps,[t(Ne,{project:a.value,onRefresh:h},null,8,["project"])])]),_:1}),t(G,{label:"需求分析",name:"analysis",disabled:!a.value.original_file},{default:o(()=>[e("div",vs,[t(wt,{"project-id":a.value.id},null,8,["project-id"])])]),_:1},8,["disabled"]),t(G,{label:"标书大纲",name:"outline",disabled:a.value.status==="created"||a.value.status==="parsing"},{default:o(()=>[e("div",ms,[t(Bt,{"project-id":a.value.id},null,8,["project-id"])])]),_:1},8,["disabled"]),t(G,{label:"标书内容",name:"document",disabled:a.value.status!=="completed"&&a.value.status!=="outline_generated"},{default:o(()=>[e("div",fs,[t(ss,{"project-id":a.value.id},null,8,["project-id"])])]),_:1},8,["disabled"])]),_:1},8,["modelValue"])])):P("",!0)])),[[ce,j.value]]),t(ue,{modelValue:y.value,"onUpdate:modelValue":r[3]||(r[3]=N=>y.value=N),title:"上传招标文件",width:"500px","before-close":L},{footer:o(()=>[e("span",$s,[t(A,{onClick:r[2]||(r[2]=N=>y.value=!1),disabled:x.value},{default:o(()=>r[11]||(r[11]=[m("取消")])),_:1,__:[11]},8,["disabled"]),t(A,{type:"primary",onClick:k,loading:x.value,disabled:!s.value},{default:o(()=>r[12]||(r[12]=[m(" 上传 ")])),_:1,__:[12]},8,["loading","disabled"])])]),default:o(()=>[e("div",gs,[t(re,{ref_key:"uploadRef",ref:n,"auto-upload":!1,limit:1,"on-change":I,"on-remove":l,"before-upload":S,drag:"",accept:".pdf,.doc,.docx"},{tip:o(()=>r[9]||(r[9]=[e("div",{class:"el-upload__tip"}," 支持 PDF、Word 格式，文件大小不超过 100MB ",-1)])),default:o(()=>[t(T,{class:"el-icon--upload"},{default:o(()=>[t(V(oe))]),_:1}),r[10]||(r[10]=e("div",{class:"el-upload__text"},[m(" 将文件拖到此处，或"),e("em",null,"点击上传")],-1))]),_:1,__:[10]},512),$.value>0?(d(),v("div",ys,[t(de,{percentage:$.value,status:g.value},null,8,["percentage","status"])])):P("",!0)])]),_:1},8,["modelValue"])])}}}),xs=W(bs,[["__scopeId","data-v-dfd4acb9"]]);export{xs as default};
