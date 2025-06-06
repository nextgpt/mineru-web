<template>
  <div class="settings-root">
    <div class="settings-card">
      <div class="settings-header">系统设置</div>
      <el-form :model="settings" label-width="120px" class="settings-form">
        <el-form-item label="强制开启OCR">
          <el-switch
            v-model="settings.forceOcr"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>
        <el-form-item label="OCR识别语言">
          <el-select v-model="settings.ocrLanguage" class="settings-select">
            <el-option label="自动识别" value="auto" />
            <el-option label="中文 & 英文" value="ch" />
            <el-option label="英语" value="en" />
            <el-option label="法语" value="fr" />
            <el-option label="德语" value="german" />
            <el-option label="日语" value="japan" />
            <el-option label="韩语" value="korean" />
            <el-option label="繁体中文" value="chinese_cht" />
            <el-option label="意大利语" value="it" />
            <el-option label="西班牙语" value="es" />
            <el-option label="葡萄牙语" value="pt" />
            <el-option label="俄语" value="ru" />
            <el-option label="乌克兰语" value="uk" />
            <el-option label="白俄罗斯语" value="be" />
            <el-option label="泰卢固语" value="te" />
            <el-option label="梵语" value="sa" />
            <el-option label="泰米尔语" value="ta" />
            <el-option label="南非荷兰语" value="af" />
            <el-option label="阿塞拜疆语" value="az" />
            <el-option label="波斯尼亚语" value="bs" />
            <el-option label="捷克语" value="cs" />
            <el-option label="威尔士语" value="cy" />
            <el-option label="丹麦语" value="da" />
            <el-option label="马耳他语" value="mt" />
            <el-option label="荷兰语" value="nl" />
            <el-option label="挪威语" value="no" />
            <el-option label="波兰语" value="pl" />
            <el-option label="罗马尼亚语" value="ro" />
            <el-option label="斯洛伐克语" value="sk" />
            <el-option label="斯洛文尼亚语" value="sl" />
            <el-option label="阿尔巴尼亚语" value="sq" />
            <el-option label="瑞典语" value="sv" />
            <el-option label="斯瓦希里语" value="sw" />
            <el-option label="他加禄语" value="tl" />
            <el-option label="土耳其语" value="tr" />
            <el-option label="乌兹别克语" value="uz" />
            <el-option label="越南语" value="vi" />
            <el-option label="蒙古语" value="mn" />
            <el-option label="阿巴扎语" value="abq" />
            <el-option label="车臣语" value="che" />
            <el-option label="哈里亚纳语" value="bgc" />
            <el-option label="阿拉伯语" value="ar" />
            <el-option label="印地语" value="hi" />
            <el-option label="维吾尔语" value="ug" />
            <el-option label="波斯语" value="fa" />
            <el-option label="乌尔都语" value="ur" />
            <el-option label="塞尔维亚语(拉丁)" value="rs_latin" />
            <el-option label="奥克西唐语" value="oc" />
            <el-option label="马拉地语" value="mr" />
            <el-option label="尼泊尔语" value="ne" />
            <el-option label="塞尔维亚语(西里尔)" value="rs_cyrillic" />
            <el-option label="保加利亚语" value="bg" />
            <el-option label="爱沙尼亚语" value="et" />
            <el-option label="爱尔兰语" value="ga" />
            <el-option label="克罗地亚语" value="hr" />
            <el-option label="匈牙利语" value="hu" />
            <el-option label="印度尼西亚语" value="id" />
            <el-option label="冰岛语" value="is" />
            <el-option label="库尔德语" value="ku" />
            <el-option label="立陶宛语" value="lt" />
            <el-option label="拉脱维亚语" value="lv" />
            <el-option label="毛利语" value="mi" />
            <el-option label="马来语" value="ms" />
            <el-option label="阿迪格语" value="ady" />
            <el-option label="卡巴尔达语" value="kbd" />
            <el-option label="阿瓦尔语" value="ava" />
            <el-option label="达尔格瓦语" value="dar" />
            <el-option label="印古什语" value="inh" />
            <el-option label="拉克语" value="lbe" />
            <el-option label="列兹金语" value="lez" />
            <el-option label="塔巴萨兰语" value="tab" />
            <el-option label="比哈尔语" value="bh" />
            <el-option label="迈蒂利语" value="mai" />
            <el-option label="昂吉卡语" value="ang" />
            <el-option label="博杰普里语" value="bho" />
            <el-option label="马加伊语" value="mah" />
            <el-option label="那格浦尔语" value="sck" />
            <el-option label="尼瓦尔语" value="new" />
            <el-option label="果阿孔卡尼语" value="gom" />
            <el-option label="巴利语" value="pi" />
            <el-option label="拉丁语" value="la" />
          </el-select>
        </el-form-item>
        <el-form-item label="公式识别">
          <el-switch
            v-model="settings.formulaRecognition"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>
        <el-form-item label="表格识别">
          <el-switch
            v-model="settings.tableRecognition"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" size="large">保存设置</el-button>
          <el-button @click="resetSettings" size="large">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getUserId } from '@/utils/user'

interface Settings {
  forceOcr: boolean
  ocrLanguage: string
  formulaRecognition: boolean
  tableRecognition: boolean
}

const defaultSettings: Settings = {
  forceOcr: false,
  ocrLanguage: 'auto',
  formulaRecognition: true,
  tableRecognition: true
}

const settings = ref<Settings>({ ...defaultSettings })

// 加载设置
const loadSettings = async () => {
  try {
    const response = await axios.get('/api/settings', {
      headers: {
        'X-User-Id': getUserId()
      }
    })

    settings.value = {
      forceOcr: response.data.force_ocr,
      ocrLanguage: response.data.ocr_lang,
      formulaRecognition: response.data.formula_recognition,
      tableRecognition: response.data.table_recognition
    }
  } catch (error: any) {
    console.error('加载设置失败:', error.response?.data || error.message)
    ElMessage.error(`加载设置失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 保存设置
const saveSettings = async () => {
  try {
    await axios.put('/api/settings', {
      force_ocr: settings.value.forceOcr,
      ocr_lang: settings.value.ocrLanguage,
      formula_recognition: settings.value.formulaRecognition,
      table_recognition: settings.value.tableRecognition,
      user_id: getUserId()
    }, {
      headers: {
        'X-User-Id': getUserId()
      }
    })

    ElMessage.success('设置已保存')
  } catch (error: any) {
    console.error('保存设置失败:', error.response?.data || error.message)
    ElMessage.error(`保存设置失败: ${error.response?.data?.detail || error.message}`)
  }
}

const resetSettings = () => {
  settings.value = { ...defaultSettings }
  ElMessage.info('设置已重置')
}

// 组件挂载时加载设置
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-root {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 32px 0 0 0;
}
.settings-card {
  width: 480px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.04);
  padding: 36px 36px 24px 36px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.settings-header {
  font-size: 1.3rem;
  font-weight: 600;
  color: #222;
  margin-bottom: 18px;
  text-align: center;
}
.settings-form {
  width: 100%;
}
.settings-select {
  width: 180px;
}
:deep(.el-form-item__content) {
  justify-content: flex-start;
}
</style> 