<template>
  <div class="app-wrapper">
    
    <!-- 🧭 顶部导航栏 -->
    <header class="top-navbar">
      <div class="brand-section">
        <span class="brand-logo">📊</span>
        <h1 class="brand-title">评估报告生成平台（test）</h1>
      </div>
      
      <div class="controls-section">
        <!-- 💡 一键高对比度浅色/暗色切换，防眼部疲劳 -->
        <button class="icon-btn" @click="toggleTheme">
          <span v-if="isLightTheme">🌙 底色切换</span>
          <span v-else>☀️ 底色切换</span>
        </button>
        <button class="icon-btn" @click="showOCR = true">📎 OCR 证据池</button>
        <button class="icon-btn" @click="showBasePriceDrawer = true">🗺️ 基准地价资料</button>
        <button class="icon-btn" @click="exportCurrentForm" :disabled="isLoading">📤 导出表单</button>
        
        <!-- 一键A4 高保真渲染预览-->
        <button class="icon-btn primary" @click="showPreview = true">📄 报告生成及预览</button>
      </div>
    </header>
    
    <!-- 🖥️ 双栏主视窗 -->
    <main class="main-viewport" 
          @dragover.prevent="handleDragOver" 
          @dragleave.prevent="handleDragLeave" 
          @drop.prevent="handleFileDrop">
      
      <!-- Excel 拖拽覆盖遮罩 -->
      <div v-if="isDragging" class="excel-drag-overlay">
        <div class="drag-icon">📥</div>
        <h2>请释放鼠标，立即一键解析测算表</h2>
        <p>系统将为您毫秒级回填 100% 对齐契约的指标</p>
      </div>
      
      <!-- ==============================================================================
           左侧：高密度表单填报区
           ============================================================================== -->
      
      <!-- 左侧导航 -->
      <aside class="sidebar-nav">
        <ul>
          <li :class="{ active: activeTab === 'p1' }" @click="activeTab = 'p1'">第一部分：报告基础</li>
          <li :class="{ active: activeTab === 'p2' }" @click="activeTab = 'p2'">第二部分：规划条件</li>
          <li :class="{ active: activeTab === 'p3' }" @click="activeTab = 'p3'">第三部分：土地权属</li>
          <li :class="{ active: activeTab === 'p4' }" @click="activeTab = 'p4'">第四部分：确价测算</li>
          <li :class="{ active: activeTab === 'p5' }" @click="openValuationProcess()">第五部分：估价过程</li>
          <li :class="{ active: activeTab === 'p6' }" @click="activeTab = 'p6'; initializeComparableLibrary()">比较实例库</li>
        </ul>
      </aside>
      <section class="left-panel work-panel">

        <div class="scroll-form-container">
          
          <!-- 📊 快捷数据源状态栏 -->
          <div class="fold-card" style="border-color: var(--accent);">
            <div class="card-body" style="grid-template-columns: 1fr; gap: 8px; padding: 12px;">
              <div style="font-size: 12px; font-weight: 700; color: var(--accent);">
                📂 智能双轨填报工作流引导：
              </div>
              <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.5;">
                1. 拖入 Excel 测算表，先建立基础指标和项目名称；<br>
                2. 打开 OCR 证据池上传附件，确认后注入依据清单和权属字段；br>
                3. 在第三部分核对热区正文、现场图片和风险提示；br>
                4. 在第四部分生成确价段落，最后打开 A4 预览导出报告。
              </div>
              <div v-if="excelMetadata.name" style="margin-top: 4px; padding: 6px; background: rgba(0,0,0,0.2); border-radius: 4px; font-size: 11px;">
                <span style="color: var(--success);">✔ 已加载测算表:</span> {{ excelMetadata.name }} <br>
                <span style="color: var(--text-secondary);">指纹MD5:</span> <code style="color: var(--accent);">{{ excelMetadata.md5.substring(0, 12) }}...</code>
              </div>
            </div>
          </div>
          
          <!-- 第一章：报告基本信息与地理区划-->
          <div v-show="activeTab === 'p1'" class="tab-pane">
            <!-- 🏷️ 顶部分类指示栏 -->
            <div class="section-title-bar">
              <span class="card-title">📊 第一部分：报告基本信息与基本参数</span>
            </div>
            
            <div class="card-body">
              <div class="form-item full-width" id="focus_item_transfer_purpose" :class="{ 'flicker-glow-active': activeFlickerField === 'transfer_purpose' }" style="display: flex; gap: 16px; margin-bottom: 12px;">
                <div id="focus_item_transfer_purpose_mode" style="flex: 1;">
                  <label class="form-label">出让/评估目的模式（ transfer_purpose_mode ）</label>
                  <select v-model="form.transfer_purpose_mode.value" @change="onTransferPurposeModeChange" :class="['field-input', getInputClass('transfer_purpose_mode'), { 'flicker-glow-active': activeFlickerField === 'transfer_purpose_mode' }]">
                    <option value="拟挂牌出让>拟挂牌出让</option>
                    <option value="办理土地使用权出让手续>办理土地使用权出让手续</option>
                    <option value="其他">其他（自定义）</option>
                  </select>
                </div>
                <div style="flex: 2;" v-if="form.transfer_purpose_mode.value === '其他'">
                  <label class="form-label">自定义出让/评估目的（ transfer_purpose ）</label>
                  <input type="text" v-model="form.transfer_purpose.value" @input="onFieldInput('transfer_purpose')" :class="['field-input', getInputClass('transfer_purpose'), { 'flicker-glow-active': activeFlickerField === 'transfer_purpose' }]" placeholder="请输入自定义出让/评估目的..." />
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_project_name">
                <label class="form-label">估价项目名称（ project_name ）</label>
                <div class="input-wrapper" style="display: flex; flex-direction: column; gap: 8px; width: 100%;">
                  <div style="display: flex; gap: 8px; width: 100%; align-items: stretch;">
                    <textarea v-model="form.project_name.value" 
                              :class="['field-input', getInputClass('project_name'), { 'flicker-glow-active': activeFlickerField === 'project_name' }]" 
                              readonly 
                              style="background-color: rgba(0,0,0,0.1); flex: 1; cursor: not-allowed; resize: none; min-height: 50px; line-height: 1.4; padding: 8px; width: 100%;" 
                              title="由各字段自动拼接生成，不可直接编辑"></textarea>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      <button @click.prevent="unlockProjectNameSuffix" class="icon-btn" style="white-space: nowrap; font-size: 12px; height: 28px;" title="修改默认后缀">修改后缀</button>
                      <span v-if="showBadge('project_name')" :class="['origin-badge', getBadgeClass('project_name')]" style="align-self: center;">
                        {{ getBadgeText('project_name') }}
                      </span>
                    </div>
                  </div>
                  <!-- 隐藏的后缀输入框，如果解锁则显示 -->
                  <div v-if="isSuffixUnlocked" id="focus_item_project_name_suffix">
                    <label class="form-label">修改后缀（ project_name_suffix ）</label>
                    <input type="text" v-model="form.project_name_suffix.value" @input="onFieldInput('project_name_suffix')" :class="['field-input', getInputClass('project_name_suffix'), { 'flicker-glow-active': activeFlickerField === 'project_name_suffix' }]" />
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_client_name">
                  <label class="form-label">委托人名称（ client_name ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_name.value" @input="onFieldInput('client_name')" 
                           :class="['field-input', getInputClass('client_name'), { 'flicker-glow-active': activeFlickerField === 'client_name' }]" />
                    <span v-if="showBadge('client_name')" :class="['origin-badge', getBadgeClass('client_name')]">
                      {{ getBadgeText('client_name') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_appraisal_org">
                  <label class="form-label">受托估价机构（ appraisal_org ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.appraisal_org.value" @input="onFieldInput('appraisal_org')" 
                           :class="['field-input', getInputClass('appraisal_org'), { 'flicker-glow-active': activeFlickerField === 'appraisal_org' }]" />
                    <span v-if="showBadge('appraisal_org')" :class="['origin-badge', getBadgeClass('appraisal_org')]">
                      {{ getBadgeText('appraisal_org') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_user">
                  <label class="form-label">土地使用者（ land_user ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_user.value" @input="onFieldInput('land_user')" 
                           :class="['field-input', getInputClass('land_user'), { 'flicker-glow-active': activeFlickerField === 'land_user' }]" />
                    <span v-if="showBadge('land_user')" :class="['origin-badge', getBadgeClass('land_user')]">
                      {{ getBadgeText('land_user') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_report_no">
                  <label class="form-label">评估报告编号（ report_no ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.report_no.value" @input="onFieldInput('report_no')" 
                           :class="['field-input', getInputClass('report_no'), { 'flicker-glow-active': activeFlickerField === 'report_no' }]" />
                    <span v-if="showBadge('report_no')" :class="['origin-badge', getBadgeClass('report_no')]">
                      {{ getBadgeText('report_no') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_report_date">
                  <label class="form-label">报告出具日期（ report_date ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.report_date.value" @input="onFieldInput('report_date')" 
                           :class="['field-input', getInputClass('report_date'), { 'flicker-glow-active': activeFlickerField === 'report_date' }]" />
                    <span v-if="showBadge('report_date')" :class="['origin-badge', getBadgeClass('report_date')]">
                      {{ getBadgeText('report_date') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_valuation_date">
                  <label class="form-label">估价期日（ valuation_date ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.valuation_date.value" @input="onFieldInput('valuation_date')" 
                           :class="['field-input', getInputClass('valuation_date'), { 'flicker-glow-active': activeFlickerField === 'valuation_date' }]" />
                    <span v-if="showBadge('valuation_date')" :class="['origin-badge', getBadgeClass('valuation_date')]">
                      {{ getBadgeText('valuation_date') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_valuation_work_date">
                <label class="form-label">现场勘查与工作日期范围（ valuation_work_date ）</label>
                <div class="input-wrapper">
                  <input type="text" v-model="form.valuation_work_date.value" @input="onFieldInput('valuation_work_date')" 
                         :class="['field-input', getInputClass('valuation_work_date'), { 'flicker-glow-active': activeFlickerField === 'valuation_work_date' }]" />
                  <span v-if="showBadge('valuation_work_date')" :class="['origin-badge', getBadgeClass('valuation_work_date')]">
                    {{ getBadgeText('valuation_work_date') }}
                  </span>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_client_org_code">
                  <label class="form-label">信用代码（ client_org_code ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_org_code.value" @input="onFieldInput('client_org_code')" 
                           :class="['field-input', getInputClass('client_org_code'), { 'flicker-glow-active': activeFlickerField === 'client_org_code' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_client_principal">
                  <label class="form-label">负责人（ client_principal ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_principal.value" @input="onFieldInput('client_principal')" 
                           :class="['field-input', getInputClass('client_principal'), { 'flicker-glow-active': activeFlickerField === 'client_principal' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_client_org_type">
                  <label class="form-label">机构性质（ client_org_type ）</label>
                  <div class="input-wrapper" style="display: flex; gap: 8px;">
                    <select v-model="form.client_org_type.value" @change="onFieldInput('client_org_type')"
                            :class="['field-input', getInputClass('client_org_type'), { 'flicker-glow-active': activeFlickerField === 'client_org_type' }]"
                            style="flex: 1;">
                      <option value="">-- 请选择机构性质 --</option>
                      <option value="政府机关">政府机关</option>
                      <option value="土地储备机构">土地储备机构</option>
                      <option value="园区管委会">园区管委会</option>
                      <option value="平台公司">平台公司</option>
                      <option value="企事业单位">企事业单位</option>
                      <option value="个人">个人</option>
                      <option value="其他">其他（手填）</option>
                    </select>
                    <input v-if="form.client_org_type.value === '其他' || !['政府机关','土地储备机构','园区管委会','平台公司','企事业单位','个人',''].includes(form.client_org_type.value)"
                           type="text" v-model="form.client_org_type.value" @input="onFieldInput('client_org_type')"
                           class="field-input" placeholder="请手填性质..." style="flex: 1.2;" />
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_client_address">
                <label class="form-label">委托方机构地址（ client_address ）</label>
                <div class="input-wrapper">
                  <input type="text" v-model="form.client_address.value" @input="onFieldInput('client_address')" 
                         :class="['field-input', getInputClass('client_address'), { 'flicker-glow-active': activeFlickerField === 'client_address' }]" />
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_client_contact">
                  <label class="form-label">联系人（ client_contact ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_contact.value" @input="onFieldInput('client_contact')" 
                           :class="['field-input', getInputClass('client_contact'), { 'flicker-glow-active': activeFlickerField === 'client_contact' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_client_phone">
                  <label class="form-label">联系电话（ client_phone ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_phone.value" @input="onFieldInput('client_phone')" 
                           :class="['field-input', getInputClass('client_phone'), { 'flicker-glow-active': activeFlickerField === 'client_phone' }]" />
                  </div>
                </div>

                <div class="form-item form-item-short" id="focus_item_client_postcode">
                  <label class="form-label">邮编（ postcode ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.client_postcode.value" @input="onFieldInput('client_postcode')" 
                           :class="['field-input', getInputClass('client_postcode'), { 'flicker-glow-active': activeFlickerField === 'client_postcode' }]" />
                  </div>
                </div>
              </div>
            </div>
          </div>


          <!-- 第二章：土地利用条件与规划限制指标-->
          <div v-show="activeTab === 'p2'" class="tab-pane">
            <!-- 🏷️ 顶部分类指示栏 -->
            <div class="section-title-bar">
              <span class="card-title">📐 第二部分：规划限制条件与土地利用指标</span>
            </div>
            
            <div class="card-body">
              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_location">
                  <label class="form-label">坐落简称（ land_location ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_location.value" @input="onFieldInput('land_location')" 
                           :class="['field-input', getInputClass('land_location'), { 'flicker-glow-active': activeFlickerField === 'land_location' }]" />
                    <span v-if="showBadge('land_location')" :class="['origin-badge', getBadgeClass('land_location')]">
                      {{ getBadgeText('land_location') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_land_plot_number">
                  <label class="form-label">地块编号（ land_plot_number ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_plot_number.value" @input="onFieldInput('land_plot_number')" 
                           :class="['field-input', getInputClass('land_plot_number'), { 'flicker-glow-active': activeFlickerField === 'land_plot_number' }]" placeholder="如：（2025018号地块）" />
                    <span v-if="showBadge('land_plot_number')" :class="['origin-badge', getBadgeClass('land_plot_number')]">
                      {{ getBadgeText('land_plot_number') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_county_name">
                  <label class="form-label">所属县市简称（ county_name ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.county_name.value" @input="onFieldInput('county_name')" 
                           :class="['field-input', getInputClass('county_name'), { 'flicker-glow-active': activeFlickerField === 'county_name' }]" />
                    <span v-if="showBadge('county_name')" :class="['origin-badge', getBadgeClass('county_name')]">
                      {{ getBadgeText('county_name') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_local_city">
                  <label class="form-label">所属市级（ local_city ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.local_city.value" @input="onFieldInput('local_city')"
                           :class="['field-input', getInputClass('local_city'), { 'flicker-glow-active': activeFlickerField === 'local_city' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_planning_approval_authority">
                  <label class="form-label">规划条件批准机关</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.planning_approval_authority.value" @input="onFieldInput('planning_approval_authority')"
                           :class="['field-input', getInputClass('planning_approval_authority'), { 'flicker-glow-active': activeFlickerField === 'planning_approval_authority' }]" />
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_location_full">
                  <label class="form-label">位置全称（ land_location_full ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_location_full.value" readonly style="background-color: rgba(0,0,0,0.1); cursor: not-allowed;" title="由简称与编号自动拼接生成" class="field-input" />
                    <span v-if="showBadge('land_location_full')" :class="['origin-badge', getBadgeClass('land_location_full')]">
                      {{ getBadgeText('land_location_full') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_technical_report_no">
                  <label class="form-label">技术报告编号（ technical_no ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.technical_report_no.value" @input="onFieldInput('technical_report_no')" 
                           :class="['field-input', getInputClass('technical_report_no'), { 'flicker-glow-active': activeFlickerField === 'technical_report_no' }]" />
                    <span v-if="showBadge('technical_report_no')" :class="['origin-badge', getBadgeClass('technical_report_no')]">
                      {{ getBadgeText('technical_report_no') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_parcel_count">
                  <label class="form-label">宗地数量（ parcel_count ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.parcel_count.value" @input="onFieldInput('parcel_count')" 
                           :class="['field-input', getInputClass('parcel_count'), { 'flicker-glow-active': activeFlickerField === 'parcel_count' }]" />
                    <span v-if="showBadge('parcel_count')" :class="['origin-badge', getBadgeClass('parcel_count')]">
                      {{ getBadgeText('parcel_count') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_area_mode">
                  <label class="form-label">面积口径（ land_area_mode ）</label>
                  <div class="input-wrapper">
                    <select v-model="form.land_area_mode.value" @change="onFieldInput('land_area_mode')"
                            :class="['field-input', getInputClass('land_area_mode'), { 'flicker-glow-active': activeFlickerField === 'land_area_mode' }]">
                      <option value="whole">整宗土地面积</option>
                      <option value="apportioned">分摊土地使用权面积</option>
                    </select>
                    <span v-if="showBadge('land_area_mode')" :class="['origin-badge', getBadgeClass('land_area_mode')]">
                      {{ getBadgeText('land_area_mode') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_land_area">
                  <label class="form-label">{{ form.land_area_mode.value === 'apportioned' ? '分摊土地使用权面积（㎡）' : '宗地面积（㎡）' }}</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_area.value" @input="onFieldInput('land_area')" 
                           :class="['field-input', getInputClass('land_area'), { 'flicker-glow-active': activeFlickerField === 'land_area' }]" />
                    <span v-if="showBadge('land_area')" :class="['origin-badge', getBadgeClass('land_area')]">
                      {{ getBadgeText('land_area') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_building_area">
                  <label class="form-label">建筑总面积（㎡）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.building_area.value" @input="onFieldInput('building_area')" 
                           :class="['field-input', getInputClass('building_area'), { 'flicker-glow-active': activeFlickerField === 'building_area' }]" />
                    <span v-if="showBadge('building_area')" :class="['origin-badge', getBadgeClass('building_area')]">
                      {{ getBadgeText('building_area') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_usage">
                  <label class="form-label">土地用途（ land_usage ）</label>
                  <div class="input-wrapper">
                    <select v-model="form.land_usage_key.value" @change="onLandUsageKeyChange" 
                            :class="['field-input', getInputClass('land_usage'), { 'flicker-glow-active': activeFlickerField === 'land_usage' }]">
                      <option v-for="opt in landUsageOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
                    </select>
                    <span v-if="showBadge('land_usage')" :class="['origin-badge', getBadgeClass('land_usage')]">
                      {{ getBadgeText('land_usage') }}
                    </span>
                  </div>
                </div>

                <div v-if="form.land_usage_key.value === 'other'" class="form-item" id="focus_item_land_usage_other">
                  <label class="form-label">其他土地用途（ other ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_usage_other.value" @input="onLandUsageOtherInput"
                           :class="['field-input', getInputClass('land_usage_other'), { 'flicker-glow-active': activeFlickerField === 'land_usage_other' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_land_use_term">
                  <label class="form-label">土地使用年限（ term ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_use_term.value" @input="onFieldInput('land_use_term')" 
                           :class="['field-input', getInputClass('land_use_term'), { 'flicker-glow-active': activeFlickerField === 'land_use_term' }]" />
                    <span v-if="showBadge('land_use_term')" :class="['origin-badge', getBadgeClass('land_use_term')]">
                      {{ getBadgeText('land_use_term') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_right_type">
                  <label class="form-label">使用权类型（ right_type ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.right_type.value" @input="onFieldInput('right_type')" 
                           :class="['field-input', getInputClass('right_type'), { 'flicker-glow-active': activeFlickerField === 'right_type' }]" />
                    <span v-if="showBadge('right_type')" :class="['origin-badge', getBadgeClass('right_type')]">
                      {{ getBadgeText('right_type') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_plot_ratio_mode">
                  <label class="form-label">规划容积率类型（ plot_ratio_mode ）</label>
                  <div class="input-wrapper">
                    <select v-model="form.plot_ratio_mode.value" @change="onPlotRatioInput('plot_ratio_mode')" 
                            :class="['field-input', getInputClass('plot_ratio_mode'), { 'flicker-glow-active': activeFlickerField === 'plot_ratio_mode' }]">
                      <option value="range">范围值</option>
                      <option value="fixed">固定值</option>
                    </select>
                  </div>
                </div>

                <div class="form-item" id="focus_item_plot_ratio">
                  <label class="form-label">{{ form.plot_ratio_mode.value === 'range' ? '规划容积率上限（ plot_ratio ）' : '规划容积率固定值（ plot_ratio ）' }}</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.plot_ratio.value" @input="onPlotRatioInput('plot_ratio')" 
                           :class="['field-input', getInputClass('plot_ratio'), { 'flicker-glow-active': activeFlickerField === 'plot_ratio' }]" />
                    <span v-if="showBadge('plot_ratio')" :class="['origin-badge', getBadgeClass('plot_ratio')]">
                      {{ getBadgeText('plot_ratio') }}
                    </span>
                  </div>
                </div>

                <div v-if="form.plot_ratio_mode.value === 'range'" class="form-item" id="focus_item_plot_ratio_min">
                  <label class="form-label">规划容积率下限（ plot_ratio_min ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.plot_ratio_min.value" @input="onPlotRatioInput('plot_ratio_min')" 
                           :class="['field-input', getInputClass('plot_ratio_min'), { 'flicker-glow-active': activeFlickerField === 'plot_ratio_min' }]" />
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_set_plot_ratio_mode">
                  <label class="form-label">设定容积率类型（ set_plot_ratio_mode ）</label>
                  <div class="input-wrapper">
                    <select v-model="form.set_plot_ratio_mode.value" @change="onSetPlotRatioInput('set_plot_ratio_mode')" 
                            :class="['field-input', getInputClass('set_plot_ratio_mode'), { 'flicker-glow-active': activeFlickerField === 'set_plot_ratio_mode' }]">
                      <option value="range">范围值</option>
                      <option value="fixed">固定值</option>
                    </select>
                  </div>
                </div>

                <div class="form-item" id="focus_item_set_plot_ratio">
                  <label class="form-label">{{ form.set_plot_ratio_mode.value === 'range' ? '设定容积率上限（ set_plot_ratio ）' : '设定容积率固定值（ set_plot_ratio ）' }}</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.set_plot_ratio.value" @input="onSetPlotRatioInput('set_plot_ratio')" 
                           :class="['field-input', getInputClass('set_plot_ratio'), { 'flicker-glow-active': activeFlickerField === 'set_plot_ratio' }]" />
                    <span v-if="showBadge('set_plot_ratio')" :class="['origin-badge', getBadgeClass('set_plot_ratio')]">
                      {{ getBadgeText('set_plot_ratio') }}
                    </span>
                  </div>
                </div>

                <div v-if="form.set_plot_ratio_mode.value === 'range'" class="form-item" id="focus_item_set_plot_ratio_min">
                  <label class="form-label">设定容积率下限（ set_plot_ratio_min ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.set_plot_ratio_min.value" @input="onSetPlotRatioInput('set_plot_ratio_min')" 
                           :class="['field-input', getInputClass('set_plot_ratio_min'), { 'flicker-glow-active': activeFlickerField === 'set_plot_ratio_min' }]" />
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_building_density_min">
                  <label class="form-label">规划建筑密度下限</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.building_density_min.value" @input="onFieldInput('building_density_min')" 
                           :class="['field-input', getInputClass('building_density_min'), { 'flicker-glow-active': activeFlickerField === 'building_density_min' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_building_density_max">
                  <label class="form-label">规划建筑密度上限</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.building_density_max.value" @input="onFieldInput('building_density_max')" 
                           :class="['field-input', getInputClass('building_density_max'), { 'flicker-glow-active': activeFlickerField === 'building_density_max' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_greening_rate">
                  <label class="form-label">规划绿地率（ greening_rate ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.greening_rate.value" @input="onFieldInput('greening_rate')" 
                           :class="['field-input', getInputClass('greening_rate'), { 'flicker-glow-active': activeFlickerField === 'greening_rate' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_building_height_limit">
                  <label class="form-label">规划建筑限高（ height_limit ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.building_height_limit.value" @input="onFieldInput('building_height_limit')" 
                           :class="['field-input', getInputClass('building_height_limit'), { 'flicker-glow-active': activeFlickerField === 'building_height_limit' }]" />
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_valuation_condition_type">
                  <label class="form-label">利用条件类型（ condition_type ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.valuation_condition_type.value" @input="onFieldInput('valuation_condition_type')" 
                           :class="['field-input', getInputClass('valuation_condition_type'), { 'flicker-glow-active': activeFlickerField === 'valuation_condition_type' }]" />
                    <span v-if="showBadge('valuation_condition_type')" :class="['origin-badge', getBadgeClass('valuation_condition_type')]">
                      {{ getBadgeText('valuation_condition_type') }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 实际和设定开发程度(并排展示) -->
              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_land_development_actual">
                  <label class="form-label">实际土地开发程度（ land_development_actual ）</label>
                  <div class="input-wrapper" style="display: flex; flex-direction: column; width: 100%;">
                    <select v-model="form.land_development_actual.value" @change="onFieldInput('land_development_actual')" 
                            :class="['field-input', getInputClass('land_development_actual'), { 'flicker-glow-active': activeFlickerField === 'land_development_actual' }]" style="width: 100%;">
                      <option v-for="opt in developmentDegreeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                    </select>
                    <span v-if="showBadge('land_development_actual')" :class="['origin-badge', getBadgeClass('land_development_actual')]">
                      {{ getBadgeText('land_development_actual') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_land_development_set">
                  <label class="form-label">设定土地开发程度（ land_development_set ）</label>
                  <div class="input-wrapper" style="display: flex; flex-direction: column; width: 100%;">
                    <select v-model="form.land_development_set.value" @change="onFieldInput('land_development_set')" 
                            :class="['field-input', getInputClass('land_development_set'), { 'flicker-glow-active': activeFlickerField === 'land_development_set' }]" style="width: 100%;">
                      <option v-for="opt in developmentDegreeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                    </select>
                    <span v-if="showBadge('land_development_set')" :class="['origin-badge', getBadgeClass('land_development_set')]">
                      {{ getBadgeText('land_development_set') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="compact-flex-row">
                <div class="form-item" id="focus_item_registered_right_type">
                  <label class="form-label">登记权利类型（ registered_right_type ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.registered_right_type.value" @input="onFieldInput('registered_right_type')" 
                           :class="['field-input', getInputClass('registered_right_type'), { 'flicker-glow-active': activeFlickerField === 'registered_right_type' }]" />
                    <span v-if="showBadge('registered_right_type')" :class="['origin-badge', getBadgeClass('registered_right_type')]">
                      {{ getBadgeText('registered_right_type') }}
                    </span>
                  </div>
                </div>

                <div class="form-item" id="focus_item_assumed_right_status">
                  <label class="form-label">设定权利状态（ assumed_right_status ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.assumed_right_status.value" @input="onFieldInput('assumed_right_status')" 
                           :class="['field-input', getInputClass('assumed_right_status'), { 'flicker-glow-active': activeFlickerField === 'assumed_right_status' }]" />
                    <span v-if="showBadge('assumed_right_status')" :class="['origin-badge', getBadgeClass('assumed_right_status')]">
                      {{ getBadgeText('assumed_right_status') }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_registered_proof_docs">
                <label class="form-label">原始权属登记的依据文书（ registered_proof_docs ）</label>
                <div class="input-wrapper">
                  <input type="text" v-model="form.registered_proof_docs.value" @input="onFieldInput('registered_proof_docs')" 
                         :class="['field-input', getInputClass('registered_proof_docs'), { 'flicker-glow-active': activeFlickerField === 'registered_proof_docs' }]" />
                  <span v-if="showBadge('registered_proof_docs')" :class="['origin-badge', getBadgeClass('registered_proof_docs')]">
                    {{ getBadgeText('registered_proof_docs') }}
                  </span>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_entrusted_source_docs">
                <label class="form-label">委托方提供资料清单（ entrusted_source_docs ）</label>
                <div class="input-wrapper">
                  <textarea v-model="form.entrusted_source_docs.value" @input="onFieldInput('entrusted_source_docs')" 
                            rows="4" :class="['field-input', getInputClass('entrusted_source_docs'), { 'flicker-glow-active': activeFlickerField === 'entrusted_source_docs' }]" style="height: auto; line-height: 1.5;"></textarea>
                  <span v-if="showBadge('entrusted_source_docs')" :class="['origin-badge', getBadgeClass('entrusted_source_docs')]" style="top: 15px;">
                    {{ getBadgeText('entrusted_source_docs') }}
                  </span>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_land_boundary_desc">
                <label class="form-label">宗地四至状况（ land_boundary_desc ）</label>
                <div class="input-wrapper">
                  <textarea v-model="form.land_boundary_desc.value" @input="onFieldInput('land_boundary_desc')" 
                            rows="2" :class="['field-input', getInputClass('land_boundary_desc'), { 'flicker-glow-active': activeFlickerField === 'land_boundary_desc' }]"></textarea>
                  <span v-if="showBadge('land_boundary_desc')" :class="['origin-badge', getBadgeClass('land_boundary_desc')]" style="top: 10px;">
                    {{ getBadgeText('land_boundary_desc') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 第三章：土地权属及原始证照（智能草稿 + 最终正文） -->
          <div v-show="activeTab === 'p3'" class="tab-pane">
            <div class="section-title-bar">
              <span class="card-title">📜 第三部分：土地权属及原始证照信息</span>
              <button class="icon-btn" style="height: 32px;" @click="showBasePriceDrawer = true">基准地价资料</button>
            </div>
            <div class="card-body">
              <div class="form-item full-width ownership-control-panel">
                <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
                  <div id="focus_item_ownership_scenario_type">
                    <label class="form-label ownership-control-label">权属情形（ ownership_scenario_type ）</label>
                    <select v-model="form.ownership_scenario_type.value" @change="onOwnershipControlChange('ownership_scenario_type')" :class="['field-input', getInputClass('ownership_scenario_type'), { 'flicker-glow-active': activeFlickerField === 'ownership_scenario_type' }]">
                      <option value="new_grant">首次出让 / 拟出让</option>
                      <option value="historical_unregistered">历史遗留未登记</option>
                      <option value="registered_complete">已登记</option>
                      <option value="mixed_manual">复杂人工</option>
                    </select>
                  </div>
                  <div>
                    <label class="form-label ownership-control-label">土地用途（引用第二部分 land_usage ）</label>
                    <select v-model="form.land_usage_key.value" @change="onLandUsageKeyChange" class="field-input">
                      <option v-for="opt in landUsageOptions" :key="`ownership_${opt.key}`" :value="opt.key">{{ opt.label }}</option>
                    </select>
                  </div>
                </div>
                 <div v-if="form.land_usage_key.value === 'other'" style="margin-top: 10px;">
                  <label class="form-label">其他土地用途（ land_usage_other ）</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.land_usage_other.value" @input="onLandUsageOtherInput" 
                           :class="['field-input', getInputClass('land_usage_other'), { 'flicker-glow-active': activeFlickerField === 'land_usage_other' }]" placeholder="例如：特殊用地、交通运输用地、仓储物流用地..." />
                  </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: center; margin-top: 10px; flex-wrap: wrap; width: 100%;">
                  <label id="focus_item_has_other_rights_limit" :class="{ 'flicker-glow-active': activeFlickerField === 'has_other_rights_limit' }" style="font-size: 12px; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;">
                    <input type="checkbox" v-model="form.has_other_rights_limit.value" @change="onOwnershipControlChange('has_other_rights_limit')" />
                    <span style="font-weight: 600; color: #e11d48;">⚠️ 存在他项权利限制</span>
                  </label>
                  <div style="flex: 1; display: flex; justify-content: flex-end; gap: 12px;">
                    <button class="icon-btn" @click.prevent="syncPerspectiveSegments">热区同步</button>
                    <button class="icon-btn" @click.prevent="regenerateOwnershipDraft(false)">同步草稿（保留人工修改）</button>
                    <button class="icon-btn primary" @click.prevent="regenerateOwnershipDraft(true)">重置为系统草稿（放弃人工修改）</button>
                  </div>
                </div>
                <div v-if="form.has_other_rights_limit.value" id="focus_item_other_rights_limit_desc" style="margin-top: 10px; width: 100%;">
                  <label class="form-label" style="color: #e11d48;">他项权利限制具体说明（ other_rights_limit_desc ）</label>
                  <div class="input-wrapper">
                    <textarea v-model="form.other_rights_limit_desc.value" @input="onFieldInput('other_rights_limit_desc')" rows="2" 
                              :class="['field-input', getInputClass('other_rights_limit_desc'), { 'flicker-glow-active': activeFlickerField === 'other_rights_limit_desc' }]" placeholder="输入限制说明，例如：估价对象已于2025年6月设置抵押权，抵押权人为中国工商银行股份有限公司..."></textarea>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_basis_docs_list">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label" style="margin-bottom: 0;">权属与规划依据文件清单（ basis_docs_list ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click.prevent="importUploadedAttachmentsToBasisDocs" title="一键智能提取右侧已成功上传解析的所有附件文件名并同步至依据清单中">
                    📋 智能引入已上传附件文件名
                  </button>
                </div>
                <div class="input-wrapper">
                  <textarea v-model="form.basis_docs_list.value" @input="onBasisDocsInput"
                            rows="4" :class="['field-input', getInputClass('basis_docs_list'), { 'flicker-glow-active': activeFlickerField === 'basis_docs_list' }]"
                            placeholder="每行一份依据文件，可粘贴批复、会议纪要、规划条件、权属证明、合同等。"></textarea>
                  <span v-if="showBadge('basis_docs_list')" :class="['origin-badge', getBadgeClass('basis_docs_list')]" style="top: 10px;">
                    {{ getBadgeText('basis_docs_list') }}
                  </span>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_land_registration_desc">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label">土地登记状况最终正文（ land_registration_desc ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="togglePerspective">
                    {{ showPerspective ? '✍ 编辑模式' : '🔍 智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper" style="width: 100%;">
                  <!-- ✍ 原装普通编辑模式 -->
                  <textarea v-show="!showPerspective" v-model="form.land_registration_desc.value" @input="onFieldInput('land_registration_desc')" 
                            rows="7" :class="['field-input', getInputClass('land_registration_desc')]"></textarea>
                  <!-- 🔍 V6.2 零v-html极速安全片段透视区，防空鲁棒性防护 -->
                  <div v-show="showPerspective" class="field-input perspective-rich-viewer">
                    <template v-if="land_registration_desc_segments && land_registration_desc_segments.length > 0">
                      <template v-for="(seg, idx) in land_registration_desc_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" 
                              :class="getDocRefClass(seg)"
                              @click="handlePerspectiveRefClick(seg)"
                              @mouseenter="showRefTooltip(seg, $event)"
                              @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.land_registration_desc.value || '（未生成正文草稿）' }}</span>
                    </template>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_land_right_desc">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label">土地权利状况最终正文（ land_right_desc ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="togglePerspective">
                    {{ showPerspective ? '✍ 编辑模式' : '🔍 智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper" style="width: 100%;">
                  <textarea v-show="!showPerspective" v-model="form.land_right_desc.value" @input="onFieldInput('land_right_desc')" 
                            rows="5" :class="['field-input', getInputClass('land_right_desc')]"></textarea>
                  <div v-show="showPerspective" class="field-input perspective-rich-viewer">
                    <template v-if="land_right_desc_segments && land_right_desc_segments.length > 0">
                      <template v-for="(seg, idx) in land_right_desc_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" 
                              :class="getDocRefClass(seg)"
                              @click="handlePerspectiveRefClick(seg)"
                              @mouseenter="showRefTooltip(seg, $event)"
                              @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.land_right_desc.value || '（未生成正文草稿）' }}</span>
                    </template>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_land_use_status_desc">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label">土地利用现状最终正文（ land_use_status_desc ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="togglePerspective">
                    {{ showPerspective ? '编辑模式' : '智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper" style="width: 100%;">
                  <textarea v-show="!showPerspective" v-model="form.land_use_status_desc.value" @input="onFieldInput('land_use_status_desc')" 
                            rows="5" :class="['field-input', getInputClass('land_use_status_desc')]"></textarea>
                  <div v-show="showPerspective" class="field-input perspective-rich-viewer">
                    <template v-if="land_use_status_desc_segments && land_use_status_desc_segments.length > 0">
                      <template v-for="(seg, idx) in land_use_status_desc_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" 
                              :class="getDocRefClass(seg)"
                              @click="handlePerspectiveRefClick(seg)"
                              @mouseenter="showRefTooltip(seg, $event)"
                              @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.land_use_status_desc.value || '（未生成正文草稿）' }}</span>
                    </template>
                  </div>
                </div>
              </div>

              <div class="form-item full-width" id="focus_item_site_photos">
                <label class="form-label">估价对象利用现状照片（可选）</label>
                <div class="site-photo-panel">
                  <div class="site-photo-actions">
                    <input type="file"
                           accept="image/*"
                           multiple
                           class="field-input"
                           @change="handleSitePhotoUpload" />
                    <span class="site-photo-hint">未上传时，Word 中不显示“估价对象利用现状如下：”。上传后自动插入图片和图注。</span>
                  </div>
                  <div v-if="sitePhotoItems.length" class="site-photo-grid">
                    <div v-for="(photo, idx) in sitePhotoItems" :key="photo.id" class="site-photo-card">
                      <img :src="photo.dataUrl" :alt="photo.name" />
                      <input type="text"
                             v-model="photo.caption"
                             class="field-input"
                             :placeholder="`图${idx + 1} 估价对象利用现状照片`" />
                      <button class="action-link danger-link" @click="removeSitePhoto(idx)">移除</button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 💡 V6.2 细节折叠面板，实现场景智能高亮置顶分区 -->
              <details class="form-item full-width" open style="border: 1px solid rgba(148,163,184,0.22); border-radius: 6px; padding: 10px; margin-top: 12px;">
                <summary style="cursor: pointer; font-size: 12px; font-weight: 700; color: var(--text-secondary);">附件识别依据与细节字段</summary>
                
                <!-- 💡 当前情形推荐录入与核对置顶高亮区 -->
                <div v-if="recommendedFields.length > 0" class="recommended-focus-grid" style="margin-top: 12px; background: rgba(0, 165, 233, 0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(14, 165, 233, 0.2); display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                  <div style="grid-column: 1 / -1; font-size: 11px; font-weight: 700; color: var(--accent); margin-bottom: 4px;">
                    💡 当前情形推荐优先核对与录入要素：
                  </div>
                  <div v-for="key in recommendedFields" :key="key" class="form-item" :id="'focus_item_' + key">
                    <label class="form-label">{{ FIELD_REGISTRY[key].label }}</label>
                    <div class="input-wrapper">
                      <template v-if="key === 'land_usage_basis' || key === 'land_area_basis'">
                        <div style="display: flex; gap: 8px; width: 100%;">
                          <input type="text" v-model="form[key].value" @input="onFieldInput(key)" :class="['field-input', getInputClass(key), { 'flicker-glow-active': activeFlickerField === key }]" style="flex: 1;" placeholder="可手填依据文件，或从右侧快捷引用..." />
                          <select v-if="basisDocsOptions.length > 0" @change="e => { if (e.target.value) { form[key].value = e.target.value; onFieldInput(key); e.target.value = ''; } }" class="field-input" style="width: auto; max-width: 130px; cursor: pointer; font-size: 11px;">
                            <option value="">📋 引用依据文件</option>
                            <option v-for="opt in basisDocsOptions" :key="opt" :value="opt">{{ opt }}</option>
                          </select>
                        </div>
                      </template>
                      <template v-else>
                        <input type="text" v-model="form[key].value" @input="onFieldInput(key)" :class="['field-input', getInputClass(key), { 'flicker-glow-active': activeFlickerField === key }]" />
                      </template>
                      <span v-if="showBadge(key)" :class="['origin-badge', getBadgeClass(key)]">{{ getBadgeText(key) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 📦 其它历史兼容细节折叠区 -->
                <details style="margin-top: 12px; border-top: 1px dashed var(--border-color); padding-top: 12px;">
                  <summary style="cursor: pointer; font-size: 11px; color: var(--text-secondary);">展示其他兼容细节要素 ({{ otherFields.length }})</summary>
                  <div class="details-grid" style="margin-top: 12px;">
                    <div v-for="key in otherFields" :key="key" class="form-item" :id="'focus_item_' + key">
                      <label class="form-label">{{ FIELD_REGISTRY[key].label }}</label>
                      <div class="input-wrapper">
                        <template v-if="key === 'land_usage_basis' || key === 'land_area_basis'">
                          <div style="display: flex; gap: 8px; width: 100%;">
                            <input type="text" v-model="form[key].value" @input="onFieldInput(key)" :class="['field-input', getInputClass(key), { 'flicker-glow-active': activeFlickerField === key }]" style="flex: 1;" placeholder="可手填依据文件，或从右侧快捷引用..." />
                            <select v-if="basisDocsOptions.length > 0" @change="e => { if (e.target.value) { form[key].value = e.target.value; onFieldInput(key); e.target.value = ''; } }" class="field-input" style="width: auto; max-width: 130px; cursor: pointer; font-size: 11px;">
                              <option value="">📋 引用依据文件</option>
                              <option v-for="opt in basisDocsOptions" :key="opt" :value="opt">{{ opt }}</option>
                            </select>
                          </div>
                        </template>
                        <template v-else>
                          <input type="text" v-model="form[key].value" @input="onFieldInput(key)" :class="['field-input', getInputClass(key), { 'flicker-glow-active': activeFlickerField === key }]" />
                        </template>
                        <span v-if="showBadge(key)" :class="['origin-badge', getBadgeClass(key)]">{{ getBadgeText(key) }}</span>
                      </div>
                    </div>
                  </div>
                </details>
              </details>
            </div>
          </div>

          <!-- 第四章：评估方法选择与加权确价-->
          <div v-show="activeTab === 'p4'" class="tab-pane">
            <!-- 🏷️ 顶部分类指示栏 -->
            <div class="section-title-bar">
              <span class="card-title">⚖️ 第四部分：确价测算与加权分配</span>
              <button class="icon-btn" style="height: 32px;" @click="showBasePriceDrawer = true">基准地价资料</button>
            </div>
            
            <div class="card-body">
              
              <!-- 🖥️ 上部：参数控制台 -->
              <div class="valuation-control-console" style="grid-column: 1 / -1; display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); padding: 20px; border-radius: 8px; margin-bottom: 24px;">
                
                <!-- 采用方法复选框（占满一整行） -->
                <div class="form-item full-width" id="focus_item_adopted_methods_summary" :class="{ 'flicker-glow-active': activeFlickerField === 'adopted_methods_summary' }" style="display: flex; flex-direction: row; gap: 16px; align-items: center; background: rgba(0,0,0,0.15); padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
                  <label class="form-label" style="font-weight: 700; margin-bottom: 0;">采用方法:</label>
                  <label id="focus_item_use_cost_approx" style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" v-model="form.use_cost_approx.value" @change="onFieldInput('use_cost_approx')" /> 成本逼近
                  </label>
                  <label id="focus_item_use_market_comp" style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" v-model="form.use_market_comp.value" @change="onFieldInput('use_market_comp')" /> 市场比较
                  </label>
                  <label id="focus_item_use_income_cap" style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" v-model="form.use_income_cap.value" @change="onFieldInput('use_income_cap')" /> 收益还原
                  </label>
                  <label id="focus_item_use_benchmark_corr" style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" v-model="form.use_benchmark_corr.value" @change="onFieldInput('use_benchmark_corr')" /> 基准系数
                  </label>
                  <label id="focus_item_use_residual" style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" v-model="form.use_residual.value" @change="onFieldInput('use_residual')" /> 剩余法
                  </label>
                </div>

                <div class="form-item full-width" id="focus_item_valuation_basis_docs_list">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <label class="form-label" style="margin-bottom: 0;">测算依据文件清单（ valuation_basis_docs_list ）</label>
                    <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click.prevent="form.valuation_basis_docs_list.value = ''; onFieldInput('valuation_basis_docs_list')" title="正式发布或异地项目可清空后重新填写">
                      清空
                    </button>
                  </div>
                  <div class="input-wrapper">
                    <textarea v-model="form.valuation_basis_docs_list.value" @input="onFieldInput('valuation_basis_docs_list')"
                              rows="4" :class="['field-input', getInputClass('valuation_basis_docs_list'), { 'flicker-glow-active': activeFlickerField === 'valuation_basis_docs_list' }]"
                              placeholder="每行一份测算依据文件，可填写征地补偿、区片价、房屋征收补偿、地方配套政策等。"></textarea>
                    <span v-if="showBadge('valuation_basis_docs_list')" :class="['origin-badge', getBadgeClass('valuation_basis_docs_list')]" style="top: 10px;">
                      {{ getBadgeText('valuation_basis_docs_list') }}
                    </span>
                  </div>
                </div>

                <!-- 🚨 智能证据预警展示区 -->
                <div v-if="activeMethodWarnings.length" class="form-item full-width" style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; width: 100%;">
                  <transition-group name="warning-list">
                    <div v-for="(warn, wIdx) in activeMethodWarnings" :key="warn.method + '_' + warn.message" 
                         :class="['warning-card-premium', warn.level]" 
                         style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-radius: 8px; border: 1px solid transparent; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                      
                      <!-- 左侧信息区-->
                      <div style="display: flex; align-items: flex-start; gap: 10px; flex: 1; padding-right: 12px;">
                        <span style="font-size: 16px; margin-top: 1px;">{{ warn.level === 'danger' ? '🚫' : '⚠️' }}</span>
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                          <span style="font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9;">
                            [{{ warn.method }} 依据预警]
                          </span>
                          <p style="font-size: 12px; margin: 0; line-height: 1.5; font-weight: 500; text-align: left;">
                            {{ warn.message }}
                          </p>
                        </div>
                      </div>

                      <!-- 右侧操作区 -->
                      <button class="warning-ack-btn" @click.prevent="acknowledgeWarning(warn.method + '_' + warn.message)" 
                              style="flex-shrink: 0; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 4px; font-weight: bold;">
                        <span>✓ 已核实，保留方法</span>
                      </button>

                    </div>
                  </transition-group>
                </div>

                <!-- 动态单价输入框组（仅在勾选时显示） -->
                <div class="form-item" id="focus_item_cost_approx_price" v-show="form.use_cost_approx.value">
                  <label class="form-label">成本逼近法单价</label>
                  <div v-if="costHasMultipleUsagePrices" class="input-wrapper">
                    <div v-for="item in costUsageResultPrices" :key="item.key" class="cost-usage-price-row">
                      <span>{{ item.label }}</span><strong>{{ item.final_price }} 元/平方米</strong>
                    </div>
                    <small>混合用途分用途单价来自第五部分测算，请在第五部分校核。</small>
                  </div>
                  <div v-else class="input-wrapper">
                    <input type="text" v-model="form.cost_approx_price.value" @input="onFieldInput('cost_approx_price')" :class="['field-input', getInputClass('cost_approx_price'), { 'flicker-glow-active': activeFlickerField === 'cost_approx_price' }]" />
                  </div>
                </div>
                
                <div class="form-item" id="focus_item_market_comp_price" v-show="form.use_market_comp.value">
                  <label class="form-label">市场比较法单价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.market_comp_price.value" @input="onFieldInput('market_comp_price')" :class="['field-input', getInputClass('market_comp_price'), { 'flicker-glow-active': activeFlickerField === 'market_comp_price' }]" />
                  </div>
                </div>
                
                <div class="form-item" id="focus_item_income_cap_price" v-show="form.use_income_cap.value">
                  <label class="form-label">收益还原法单价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.income_cap_price.value" @input="onFieldInput('income_cap_price')" :class="['field-input', getInputClass('income_cap_price'), { 'flicker-glow-active': activeFlickerField === 'income_cap_price' }]" />
                  </div>
                </div>
                
                <div class="form-item" id="focus_item_benchmark_corr_price" v-show="form.use_benchmark_corr.value">
                  <label class="form-label">基准地价系数修正单价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.benchmark_corr_price.value" @input="onFieldInput('benchmark_corr_price')" :class="['field-input', getInputClass('benchmark_corr_price'), { 'flicker-glow-active': activeFlickerField === 'benchmark_corr_price' }]" />
                  </div>
                </div>
                
                <div class="form-item" id="focus_item_residual_price" v-show="form.use_residual.value">
                  <label class="form-label">剩余法单价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.residual_price.value" @input="onFieldInput('residual_price')" :class="['field-input', getInputClass('residual_price'), { 'flicker-glow-active': activeFlickerField === 'residual_price' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_final_unit_price">
                  <label class="form-label">系统最终评估地面单价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.final_unit_price.value" :readonly="!form.requires_manual_final_price.value" @input="onFieldInput('final_unit_price')" :class="['field-input', getInputClass('final_unit_price'), { 'flicker-glow-active': activeFlickerField === 'final_unit_price' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_final_total_price">
                  <label class="form-label">系统最终评估土地总价</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.final_total_price.value" :readonly="!form.requires_manual_final_price.value" @input="onFieldInput('final_total_price')" :class="['field-input', getInputClass('final_total_price'), { 'flicker-glow-active': activeFlickerField === 'final_total_price' }]" />
                  </div>
                </div>

                <div class="form-item" id="focus_item_final_total_price_upper">
                  <label class="form-label">系统最终土地总价大写</label>
                  <div class="input-wrapper">
                    <input type="text" v-model="form.final_total_price_upper.value" :readonly="!form.requires_manual_final_price.value" @input="onFieldInput('final_total_price_upper')" :class="['field-input', getInputClass('final_total_price_upper'), { 'flicker-glow-active': activeFlickerField === 'final_total_price_upper' }]" />
                  </div>
                </div>

                <!-- 核心确价分配参数 -->
                <div class="form-item full-width" id="focus_item_weight_logic_type">
                  <label class="form-label">确价加权逻辑（weight_logic_type）</label>
                  <div class="weight-logic-line">
                    <select v-model="form.weight_logic_type.value" @change="onWeightLogicChange" class="field-input weight-logic-select">
                      <option value="weighted_average">加权算术平均（weighted_average）</option>
                      <option value="median">中位数（median）</option>
                      <option value="mode">众数（mode）</option>
                    </select>
                    <div class="weight-grid" id="focus_item_method_weight_percentages" v-show="form.weight_logic_type.value === 'weighted_average'">
                      <div v-for="item in selectedValuationMethods" :key="item.flag" class="weight-row">
                        <span>{{ item.name }}</span>
                        <input type="number" min="0" max="100" step="0.01"
                               v-model="form.method_weight_percentages.value[item.flag]"
                               @input="onMethodWeightInput"
                               class="field-input" />
                        <span>%</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 基准地价时效与控制操作组漂亮整合 -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 6px; margin-top: 12px; flex-wrap: wrap; gap: 12px; width: 100%; grid-column: 1 / -1;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 12px; font-weight: 700;">📅 基准地价时效:</span>
                    <span style="font-size: 12px; color: var(--text-secondary);">{{ basePriceExpiryStatusText }}</span>
                  </div>
                  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button class="icon-btn" style="padding: 6px 12px; font-size: 12px;" @click.prevent="syncValuationSegments" title="同步计算公式及参数热区">热区同步</button>
                    <button class="icon-btn" style="padding: 6px 12px; font-size: 12px;" @click.prevent="regenerateValuationNarratives(false)" title="同步测算草稿文本，保留您在编辑区做过的人工改动">同步草稿</button>
                    <button class="icon-btn primary" style="padding: 6px 12px; font-size: 12px;" @click.prevent="regenerateValuationNarratives(true)" title="清空全部人工改动，完全重置为系统自动生成的草稿文本">重置系统草稿</button>
                  </div>
                </div>
              </div>

              <!-- 🖥️ 下部：五大条目化最终正文草稿（双轨热区透视） -->
              
              <!-- 1. 选用方法及适用性说明-->
              <div class="form-item full-width" style="margin-top: 10px;" id="focus_item_valuation_method_reasons">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label" style="color: var(--accent); font-weight: 700;">📝 新要素①：估价方法选用及适用性说明最终正文（ valuation_method_reasons ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="toggleValuationPerspective">
                    {{ showValuationPerspective ? '✍ 编辑模式' : '🔍 智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper">
                  <textarea v-model="form.valuation_method_reasons.value" @input="onFieldInput('valuation_method_reasons')"
                            v-show="!showValuationPerspective"
                            rows="6" :class="['field-input', getInputClass('valuation_method_reasons'), { 'flicker-glow-active': activeFlickerField === 'valuation_method_reasons' }]"
                            style="height: auto; font-family: inherit; line-height: 1.6;"></textarea>
                  <div v-show="showValuationPerspective" class="field-input perspective-rich-viewer valuation-rich-viewer">
                    <template v-if="valuation_method_reasons_segments && valuation_method_reasons_segments.length > 0">
                      <template v-for="(seg, idx) in valuation_method_reasons_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" :class="getDocRefClass(seg)" @click="handlePerspectiveRefClick(seg)" @mouseenter="showRefTooltip(seg, $event)" @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.valuation_method_reasons.value || '（未生成确价方法与适用性说明草稿）' }}</span>
                    </template>
                  </div>
                  <span v-if="showBadge('valuation_method_reasons')" :class="['origin-badge', getBadgeClass('valuation_method_reasons')]" style="top: 15px;">
                    {{ getBadgeText('valuation_method_reasons') }}
                  </span>
                </div>
              </div>

              <!-- 2. 地价确定及加权确价理由-->
              <div class="form-item full-width" style="margin-top: 10px;" id="focus_item_final_price_determination">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label" style="color: var(--accent); font-weight: 700;">📝 新要素②：地价确定及加权确价理由最终正文（ final_price_determination ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="toggleValuationPerspective">
                    {{ showValuationPerspective ? '✍ 编辑模式' : '🔍 智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper">
                  <textarea v-model="form.final_price_determination.value" @input="onFieldInput('final_price_determination')" 
                            v-show="!showValuationPerspective"
                            rows="6" :class="['field-input', getInputClass('final_price_determination'), { 'flicker-glow-active': activeFlickerField === 'final_price_determination' }]"
                            style="height: auto; font-family: inherit; line-height: 1.6;"></textarea>
                  <div v-show="showValuationPerspective" class="field-input perspective-rich-viewer valuation-rich-viewer">
                    <template v-if="final_price_determination_segments && final_price_determination_segments.length > 0">
                      <template v-for="(seg, idx) in final_price_determination_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" :class="getDocRefClass(seg)" @click="handlePerspectiveRefClick(seg)" @mouseenter="showRefTooltip(seg, $event)" @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.final_price_determination.value || '（未生成确价理由及开发程度草稿）' }}</span>
                    </template>
                  </div>
                  <span v-if="showBadge('final_price_determination')" :class="['origin-badge', getBadgeClass('final_price_determination')]" style="top: 15px;">
                    {{ getBadgeText('final_price_determination') }}
                  </span>
                </div>
              </div>

              <!-- 3. 确定估价结果正文 -->
              <div class="form-item full-width" style="margin-top: 10px;" id="focus_item_valuation_result_statement">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="form-label" style="color: var(--accent); font-weight: 700;">📝 新要素③：确定估价结果最终正文（ valuation_result_statement ）</label>
                  <button class="icon-btn" style="font-size: 11px; padding: 2px 6px; height: auto;" @click="toggleValuationPerspective">
                    {{ showValuationPerspective ? '✍ 编辑模式' : '🔍 智能热区透视' }}
                  </button>
                </div>
                <div class="input-wrapper">
                  <textarea v-model="form.valuation_result_statement.value" @input="onFieldInput('valuation_result_statement')"
                            v-show="!showValuationPerspective"
                            rows="7" :class="['field-input', getInputClass('valuation_result_statement'), { 'flicker-glow-active': activeFlickerField === 'valuation_result_statement' }]"
                            style="height: auto; font-family: inherit; line-height: 1.6;"></textarea>
                  <div v-show="showValuationPerspective" class="field-input perspective-rich-viewer valuation-rich-viewer">
                    <template v-if="valuation_result_statement_segments && valuation_result_statement_segments.length > 0">
                      <template v-for="(seg, idx) in valuation_result_statement_segments" :key="idx">
                        <span v-if="seg.field || seg.fields" :class="getDocRefClass(seg)" @click="handlePerspectiveRefClick(seg)" @mouseenter="showRefTooltip(seg, $event)" @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                        <span v-else>{{ seg.text }}</span>
                      </template>
                    </template>
                    <template v-else>
                      <span>{{ form.valuation_result_statement.value || '（未生成确定估价结果草稿）' }}</span>
                    </template>
                  </div>
                  <span v-if="showBadge('valuation_result_statement')" :class="['origin-badge', getBadgeClass('valuation_result_statement')]" style="top: 15px;">
                    {{ getBadgeText('valuation_result_statement') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-show="activeTab === 'p5'" class="tab-pane valuation-process-workspace">
            <div class="section-title-bar">
              <span class="card-title">第五部分：估价过程正文校核</span>
              <div class="process-toolbar">
                <button :class="['icon-btn', { primary: processViewMode === 'edit' }]" @click="processViewMode = 'edit'">编辑模式</button>
                <button :class="['icon-btn', { primary: processViewMode === 'hotspot' }]" @click="processViewMode = 'hotspot'">热区透视</button>
                <button class="icon-btn primary" @click="loadValuationProcessDraft">同步系统草稿</button>
              </div>
            </div>

            <div v-if="!valuationProcessDraft.methods?.length" class="process-empty">
              第四部分尚未勾选估价方法。
              <button class="table-action" @click="activeTab = 'p4'">前往第四部分</button>
            </div>
            <template v-else>
              <div class="process-method-tabs">
                <button v-for="method in valuationProcessDraft.methods" :key="method.method_key"
                        :class="['icon-btn', { primary: activeProcessMethodKey === method.method_key }]"
                        @click="activeProcessMethodKey = method.method_key">
                  {{ method.name }}
                  <span :class="['process-state-dot', method.status]"></span>
                </button>
              </div>

              <section v-if="activeProcessMethod" class="process-method-overview">
                <div class="process-status-band">
                  <div><span>当前方法</span><strong>{{ activeProcessMethod.name }}</strong></div>
                  <div><span>完成状态</span><strong>{{ processStatusLabel(activeProcessMethod.status) }}</strong></div>
                  <div><span>正文段落</span><strong>{{ activeProcessMethod.narratives?.length || 0 }}</strong></div>
                  <div><span>结构化表格</span><strong>{{ activeProcessMethod.tables?.length || 0 }}</strong></div>
                </div>

                <div v-if="activeProcessMethod.warnings?.length" class="analysis-warnings process-warnings">
                  <div v-for="warning in activeProcessMethod.warnings" :key="warning.message" class="warning-reference-line">
                    <span>{{ warning.message }}</span>
                    <button v-if="warningActionLabel(warning)" class="warning-hotspot" @click="handleWarningAction(warning)">
                      热区：{{ warningActionLabel(warning) }}
                    </button>
                  </div>
                </div>

                <template v-if="activeProcessMethod.method_key === 'cost_approx'">
                  <div class="market-workspace-tabs">
                    <button v-for="item in costWorkspaceViews" :key="item.key"
                            :class="['icon-btn', { primary: costWorkspaceView === item.key }]"
                            @click="costWorkspaceView = item.key">
                      {{ item.label }}
                    </button>
                  </div>

                  <section v-if="costWorkspaceView === 'policy'" id="focus_item_cost_approx_policy" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>政策依据与征收地类</strong>
                      <label id="focus_item_acquisition_land_class" :class="{ 'flicker-glow-active': activeFlickerField === 'acquisition_land_class' }">征收一级类
                        <select v-model="form.acquisition_land_class.value" class="field-input" @change="onAcquisitionLandClassChange">
                          <option v-for="(_, landClass) in acquisitionLandClassTree" :key="landClass" :value="landClass">{{ landClass }}</option>
                        </select>
                      </label>
                      <label id="focus_item_acquisition_land_subclass" :class="{ 'flicker-glow-active': activeFlickerField === 'acquisition_land_subclass' }">费用计算细分类
                        <select v-model="form.acquisition_land_subclass.value" class="field-input" @change="onAcquisitionLandSubclassChange">
                          <option v-for="subclass in acquisitionLandSubclassOptions" :key="subclass" :value="subclass">{{ subclass }}</option>
                        </select>
                      </label>
                      <label id="focus_item_acquisition_land_class_confirmed" class="cost-land-class-confirm"><input type="checkbox" v-model="form.acquisition_land_class_confirmed.value" class="confirm-checkbox" /> 已确认征收地类</label>
                      <label :id="costFocusId('compensation_zone')" :class="costFocusClass('compensation_zone')">征地区片
                        <select v-model="costAnalysis.compensation_zone" class="field-input compact-input" @change="onCostCompensationZoneChange">
                          <option value="Ⅰ区">Ⅰ区</option>
                          <option value="Ⅱ区">Ⅱ区</option>
                          <option value="Ⅲ区">Ⅲ区</option>
                        </select>
                      </label>
                      <button v-if="costZoneSuggestionAvailable && costAnalysis.compensation_zone_override" class="table-action" @click="applyCostZoneSuggestion">采用区片推荐</button>
                      <button class="icon-btn primary" @click="rematchCostApproximation">重新匹配并计算</button>
                    </div>
                    <div v-if="costZoneSuggestionSummary" :id="costFocusId('compensation_zone_suggestion')" :class="['cost-zone-suggestion', costFocusClass('compensation_zone_suggestion')]">
                      <strong>区片划分表推荐</strong>
                      <span>{{ costZoneSuggestionSummary }}</span>
                      <small v-if="costAnalysis.compensation_zone_suggestion?.source_path">{{ costAnalysis.compensation_zone_suggestion.source_path.split(/[/\\]/).pop() }}</small>
                    </div>
                    <div class="analysis-summary-strip">
                      <div><span>所属县市</span><strong>{{ textValue('county_name', '待填写') }}</strong><small>用于匹配省级区片标准</small></div>
                      <div :id="costFocusId('effective_local_city')" :class="costFocusClass('effective_local_city')"><span>自动匹配市级</span><strong>{{ costAnalysis.effective_local_city || textValue('local_city', '待匹配') }}</strong><small>由所属县市自动判断</small></div>
                      <div><span>征收一级类</span><strong>{{ textValue('acquisition_land_class', '待填写') }}</strong><small>用于成本法正文</small></div>
                      <div><span>费用细分类</span><strong>{{ textValue('acquisition_land_subclass', '待填写') }}</strong><small>用于青苗、地类系数和税费</small></div>
                      <div><span>征地区片</span><strong>{{ costAnalysis.compensation_zone || 'Ⅰ区' }}</strong><small>{{ costAnalysis.compensation_zone_override ? '已人工覆盖推荐' : '按坐落自动推荐' }}</small></div>
                      <div :id="costFocusId('green_seedling_standard_per_mu')" :class="costFocusClass('green_seedling_standard_per_mu')"><span>青苗补偿标准</span><strong>{{ costAnalysis.green_seedling_standard_per_mu || '待匹配' }}</strong><small>{{ costAnalysis.green_seedling_standard_source || '按征收地类匹配' }}</small></div>
                      <div><span>政策文件</span><strong>{{ costAnalysis.policy_documents?.length || 0 }}</strong><small>报告采用时冻结</small></div>
                    </div>
                    <div class="cost-bulk-toolbar">
                      <button class="table-action" @click="confirmCostPolicies">全部确认政策</button>
                    </div>
                    <h4 class="cost-policy-subtitle">系统推荐政策</h4>
                    <div class="cost-policy-list">
                      <label v-for="doc in costSystemPolicies" :key="doc.key" :id="costFocusId('policy_documents.' + doc.key)" :class="['cost-policy-row', costFocusClass('policy_documents.' + doc.key)]">
                        <input type="checkbox" v-model="doc.confirmed" class="confirm-checkbox" />
                        <span><strong>{{ doc.name }}</strong><small>{{ doc.document_no }} ｜ {{ doc.region }} ｜ {{ doc.effective_date || '生效日期待校核' }}</small></span>
                        <em>{{ doc.enabled === false ? '已被替换' : doc.confirmed ? '已确认' : '待确认' }}</em>
                      </label>
                    </div>
                    <h4 class="cost-policy-subtitle">测算依据文件清单</h4>
                    <div class="cost-attachment-inventory">
                      <p v-if="!costBasisAttachmentInventory.length" class="muted-text">当前县市暂无已结构化收集的测算依据文件，请对照政策原件补充。</p>
                      <div v-else class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead>
                            <tr><th>类别</th><th>文件</th><th>适用县市</th><th>结构化状态</th><th>价格字段</th><th>下一步</th></tr>
                          </thead>
                          <tbody>
                            <tr v-for="(item, index) in costBasisAttachmentInventory" :key="`cost_basis_file_${index}`"
                                :id="costFocusId('cost_basis_attachment_inventory.' + (item.target_key || index))"
                                :class="costFocusClass('cost_basis_attachment_inventory.' + (item.target_key || index))">
                              <td>{{ item.category || '政策附件' }}</td>
                              <td>
                                <strong>{{ item.label }}</strong>
                                <small v-if="item.source_path">{{ item.source_path.split(/[/\\]/).pop() }}</small>
                              </td>
                              <td>{{ costAttachmentCounties(item) }}</td>
                              <td><span :class="['cost-status-pill', costAttachmentStructuredStatusClass(item)]">{{ costAttachmentStructuredStatus(item) }}</span></td>
                              <td>
                                <div v-if="costAttachmentPriceFields(item).length" class="cost-price-field-links">
                                  <button v-for="field in costAttachmentPriceFields(item)" :key="field" type="button" class="table-action compact-action" @click="focusNestedProcessField(field)">
                                    {{ costAttachmentFieldLabel(field) }}
                                  </button>
                                </div>
                                <button v-else-if="item.target_ref" type="button" class="table-action compact-action" @click="focusNestedProcessField(item.target_ref)">
                                  前往来源
                                </button>
                                <span v-else>—</span>
                                <small v-if="item.structured_item_count">{{ item.structured_item_count }} 项</small>
                              </td>
                              <td>{{ item.next_action || costAttachmentStatus(item) }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    <h4 class="cost-policy-subtitle">当前采用政策与补充依据</h4>
                    <div class="cost-policy-list">
                      <label v-for="doc in costAdoptedPolicies.filter(item => item.source_type !== 'system_recommendation')" :key="doc.key" :id="costFocusId('policy_documents.' + doc.key)" :class="['cost-policy-row', costFocusClass('policy_documents.' + doc.key)]">
                        <input type="checkbox" v-model="doc.confirmed" class="confirm-checkbox" />
                        <span><strong>{{ doc.name }}</strong><small>{{ doc.role === 'supplemental' ? '补充依据，不改变计算' : `替换 ${doc.replaces_key || '当前政策'}` }} ｜ {{ doc.note || '无备注' }}</small></span>
                        <em>{{ doc.confirmed ? '已确认' : '待确认' }}</em>
                      </label>
                    </div>
                    <section class="cost-item-group cost-policy-compose" id="focus_item_cost_tax_basis_docs">
                      <header><div><strong>引用或新增政策依据</strong><small>默认作为补充依据；仅明确选择替换对象时影响费用标准。</small></div></header>
                      <div class="cost-policy-compose-grid">
                        <label>引用共享依据<select class="field-input" @change="e => { applyCostPolicyReference(e.target.value); e.target.value = '' }"><option value="">搜索并引用已有依据</option><option v-for="option in sharedBasisReferenceOptions" :key="`cost_policy_${option}`" :value="option">{{ option }}</option></select></label>
                        <label>政策名称<input v-model="costPolicyDraft.name" class="field-input" /></label>
                        <label>政策文号<input v-model="costPolicyDraft.document_no" class="field-input" /></label>
                        <label>作用类型<select v-model="costPolicyDraft.role" class="field-input"><option value="supplemental">补充说明依据</option><option value="province_compensation">省级征地补偿政策</option><option value="local_compensation">市县配套补偿政策</option><option value="tax_policy">税费政策</option></select></label>
                        <label>替换当前政策<select v-model="costPolicyDraft.replaces_key" class="field-input"><option value="">不替换，仅补充</option><option v-for="doc in costSystemPolicies.filter(item => item.enabled !== false)" :key="`replace_${doc.key}`" :value="doc.key">{{ doc.name }}</option></select></label>
                        <label>备注<input v-model="costPolicyDraft.note" class="field-input" placeholder="说明适用范围或替换原因" /></label>
                      </div>
                      <div class="basis-reference-actions"><button class="table-action" @click="addSharedValuationBasis(costPolicyDraft.name || costPolicyDraft.reference_text)">加入共享测算依据</button><button class="icon-btn primary" @click="addCostPolicyDocument">加入当前报告</button></div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>市级/县级配套补偿政策</strong><small>道县自动推荐永州市现行办法；其他县市由估价师补充并确认。</small></div></header>
                      <div class="cost-external-import cost-policy-editor">
                        <label id="focus_item_local_compensation_policy_name">政策名称<input v-model="form.local_compensation_policy_name.value" class="field-input" @change="calculateCostApproximation" /></label>
                        <label id="focus_item_local_compensation_policy_no">政策文号<input v-model="form.local_compensation_policy_no.value" class="field-input" @change="calculateCostApproximation" /></label>
                        <label id="focus_item_local_compensation_policy_date">发布日期<input v-model="form.local_compensation_policy_date.value" class="field-input" @change="calculateCostApproximation" /></label>
                      </div>
                    </section>
                  </section>

                  <section v-if="costWorkspaceView === 'costs'" id="focus_item_cost_approx_analysis" :class="['market-workspace-panel', { 'flicker-glow-active': activeFlickerField === 'cost_approx_analysis' }]">
                    <div class="analysis-toolbar">
                      <strong>费用测算流水</strong>
                      <span>推荐值可以参与试算，但正式归档前必须逐项确认。</span>
                      <button class="icon-btn primary" @click="calculateCostApproximation">计算并校核</button>
                      <button class="icon-btn" type="button" @click="openCostPricingAssistant">调价助手</button>
                    </div>
                    <div class="analysis-summary-strip">
                      <div :id="costFocusId('totals.acquisition_total')" :class="costFocusClass('totals.acquisition_total')"><span>土地取得费</span><strong>{{ costAnalysis.totals?.acquisition_total || '待计算' }}</strong><small>元/平方米</small></div>
                      <div :id="costFocusId('totals.tax_total')" :class="costFocusClass('totals.tax_total')"><span>相关税费</span><strong>{{ costAnalysis.totals?.tax_total || '待计算' }}</strong><small>元/平方米</small></div>
                      <div :id="costFocusId('totals.acquisition_and_tax_total')" :class="costFocusClass('totals.acquisition_and_tax_total')"><span>取得费及税费合计</span><strong>{{ costAnalysis.totals?.acquisition_and_tax_total || '待计算' }}</strong><small>元/平方米</small></div>
                      <div :id="costFocusId('totals.development_total')" :class="costFocusClass('totals.development_total')"><span>土地开发费</span><strong>{{ costAnalysis.totals?.development_total || '待计算' }}</strong><small>元/平方米</small></div>
                      <div :id="costFocusId('totals.interest')" :class="costFocusClass('totals.interest')"><span>投资利息</span><strong>{{ costAnalysis.totals?.interest || '待计算' }}</strong><small>元/平方米</small></div>
                    </div>
                    <nav class="cost-flow-nav" aria-label="费用测算分区">
                      <span class="cost-flow-nav-label">快速跳转</span>
                      <button v-for="anchor in costFlowAnchors" :key="anchor.id" type="button" class="table-action" @click="scrollToCostSection(anchor.id)">{{ anchor.label }}</button>
                    </nav>
                    <section id="cost-section-population" class="cost-item-group cost-population-group">
                      <header>
                        <div><strong>平均安置农业人口数</strong><small>对应正式报告表3-2；输入用地面积与农业人口后自动折合并计算平均值。</small></div>
                        <div class="cost-header-actions">
                          <button class="table-action" @click="addCostPopulationCase">新增案例</button>
                          <button class="table-action" @click="confirmCostPopulationCases">全部确认</button>
                        </div>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>项目名称</th><th>位置</th><th>用地面积（公顷）</th><th>安置农业人口（人）</th><th>安置人口数折合人/公顷</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="(item, index) in costAnalysis.resettlement_population_cases || []" :key="item.key || index">
                              <td><input v-model="item.name" :id="costFocusId('resettlement_population_cases.' + index + '.name')" class="field-input" /></td>
                              <td><input v-model="item.location" :id="costFocusId('resettlement_population_cases.' + index + '.location')" class="field-input" /></td>
                              <td><input v-model="item.land_area_ha" :id="costFocusId('resettlement_population_cases.' + index + '.land_area_ha')" class="field-input compact-input" @input="onCostPopulationCaseInput(item)" /></td>
                              <td><input v-model="item.population" :id="costFocusId('resettlement_population_cases.' + index + '.population')" class="field-input compact-input" @input="onCostPopulationCaseInput(item)" /></td>
                              <td :id="costFocusId('resettlement_population_cases.' + index + '.population_per_ha')" :class="costFocusClass('resettlement_population_cases.' + index + '.population_per_ha')">{{ costPopulationPerHa(item) || '待计算' }}</td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                          <tfoot>
                            <tr><td>平均值</td><td>/</td><td>/</td><td>/</td><td>{{ costPopulationAverage || '待计算' }}</td><td></td></tr>
                          </tfoot>
                        </table>
                      </div>
                    </section>
                    <section id="cost-section-building" class="cost-item-group cost-building-group">
                      <header>
                        <div><strong>建筑物补偿标准</strong><small>表3-1 各行合计为 <strong>元/人</strong>；表3-2 平均人口密度折算为 <strong>元/平方米</strong> 进入土地取得费。改表3-1/3-2 会即时重算行金额与取得费摘要。</small></div>
                        <div class="cost-header-actions">
                          <button class="cost-help-icon-btn" type="button" title="政策标准一览" aria-label="政策标准一览" @click="openCostBuildingCompensationHelp">?</button>
                          <button class="table-action" @click="addCostBuildingCompensationRow">从政策目录添加</button>
                          <button class="table-action" @click="confirmCostBuildingCompensation">全部确认</button>
                        </div>
                      </header>
                      <p v-if="costBuildingPopulationMissing" class="cost-inline-warning">表3-1 已合计{{ costAnalysis.attachment_compensation_analysis?.building_compensation_per_person || '0.00' }} 元/人，但表3-2 尚未填写有效安置人口案例，地上建筑物补偿进入取得费的金额暂为 0.00 元/平方米。</p>
                      <!-- i2：表3-1/3-2 中间测算为各字段唯一来源（含后端 narrative 热区锚点）；
                           土地取得费脚注不再重复地上附着物明细，避免与本表重复。 -->
                      <p class="cost-derived-summary-line">
                        <span :id="costFocusId('attachment_compensation_analysis.building_compensation_per_person')" :class="costFocusClass('attachment_compensation_analysis.building_compensation_per_person')">建筑物平均补偿{{ costAnalysis.attachment_compensation_analysis?.building_compensation_per_person || '待计算' }} 元/人</span>
                        <span :id="costFocusId('attachment_compensation_analysis.average_population_per_ha')" :class="costFocusClass('attachment_compensation_analysis.average_population_per_ha')">平均安置农业人口 {{ costPopulationAverage || costAnalysis.attachment_compensation_analysis?.average_population_per_ha || '待计算' }} 人/公顷</span>
                        <span :id="costFocusId('attachment_compensation_analysis.green_seedling_per_sqm')" :class="costFocusClass('attachment_compensation_analysis.green_seedling_per_sqm')">青苗折合 {{ costAnalysis.attachment_compensation_analysis?.green_seedling_per_sqm || '待计算' }} 元/平方米</span>
                        <span :id="costFocusId('attachment_compensation_analysis.attachment_compensation_per_sqm')" :class="costFocusClass('attachment_compensation_analysis.attachment_compensation_per_sqm')">地上附着物折合{{ costAnalysis.attachment_compensation_analysis?.attachment_compensation_per_sqm || '待计算' }} 元/平方米</span>
                      </p>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>补偿项目名称</th><th>附着物补偿标准</th><th>计算基数</th><th>人均合法建筑面积/数量</th><th>补偿金额（元）</th><th>备注</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="(item, index) in costAnalysis.building_compensation_rows || []" :key="item.key || index">
                              <td><input v-model="item.label" :id="costFocusId('building_compensation_rows.' + index + '.label')" class="field-input" /></td>
                              <td><div class="cost-inline-standard"><input v-model="item.standard" :id="costFocusId('building_compensation_rows.' + index + '.standard')" class="field-input compact-input" :readonly="buildingRowStandardReadonly(item)" :title="buildingRowStandardReadonly(item) ? '已与政策文件校验一致，如需调整请改级别或联系管理员更新配置' : ''" @input="onBuildingCompensationRowInput(item)" /><span>{{ item.standard_unit || item.unit }}</span></div></td>
                              <td><input v-model="item.calculation_basis" :id="costFocusId('building_compensation_rows.' + index + '.calculation_basis')" class="field-input" @input="onBuildingCompensationRowInput(item)" /></td>
                              <td><input v-model="item.quantity" :id="costFocusId('building_compensation_rows.' + index + '.quantity')" class="field-input compact-input" @input="onBuildingCompensationRowInput(item)" /></td>
                              <td :id="costFocusId('building_compensation_rows.' + index + '.amount')" :class="costFocusClass('building_compensation_rows.' + index + '.amount')">{{ item.amount || '待计算' }}</td>
                              <td>
                                <span class="cost-report-note">{{ buildingRowReportNote(item) || '—' }}</span>
                              </td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section v-for="group in costItemGroups" :id="'cost-section-acquisition'" :key="group.key" :class="['cost-item-group', 'cost-' + group.key]">
                      <header>
                        <div><strong>{{ group.label }}</strong><small>{{ costConfirmedCount(group.key) }} / {{ visibleCostItems(group.key).filter(item => item.enabled !== false).length }} 已确认；表3-1/3-2 填写后此处自动汇总。</small></div>
                        <button class="table-action" @click="confirmCostGroup(group.key)">全部确认</button>
                      </header>
                      <p v-if="costLandCompensationZoneHint" class="cost-inline-warning">{{ costLandCompensationZoneHint }}</p>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>采用</th><th>项目</th><th>等别/口径</th><th>标准值</th><th>系数</th><th>金额（元/㎡）</th><th>依据/说明</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="item in visibleCostItems(group.key)" :key="item.key"
                                :id="costFocusId(group.key + '.' + item.key)"
                                :class="costFocusClass(group.key + '.' + item.key)">
                              <td><input type="checkbox" v-model="item.enabled" class="confirm-checkbox" @change="onCostItemEnabledChange(item)" /></td>
                              <td><input v-model="item.label" :id="costFocusId(group.key + '.' + item.key + '.label')" :class="['field-input', costFocusClass(group.key + '.' + item.key + '.label')]" @input="markCostItemEdited(item)" /></td>
                              <td>
                                <select v-if="costGradeOptions(item).length" v-model="item.grade_name" :id="costFocusId(group.key + '.' + item.key + '.grade_name')" :class="['field-input compact-input', costFocusClass(group.key + '.' + item.key + '.grade_name')]" @change="onCostGradeChange(item)">
                                  <option value="">请选择</option>
                                  <option v-for="option in costGradeOptions(item)" :key="option" :value="option">{{ option }}</option>
                                </select>
                                <span v-else class="cost-na-chip">无</span>
                              </td>
                              <td><input v-model="item.standard_value" :id="costFocusId(group.key + '.' + item.key + '.standard_value')" :class="['field-input compact-input', costFocusClass(group.key + '.' + item.key + '.standard_value')]" :placeholder="costItemStandardPlaceholder(item)" @input="onCostItemValueInput(item)" /></td>
                              <td>
                                <span v-if="costItemCoefficientHint(item)" class="cost-na-chip" :title="'0.0015 为元/亩折算元/平方米的固定单位换算系数'">{{ costItemCoefficientHint(item) }}</span>
                                <span v-else class="cost-na-chip">无独立系数</span>
                              </td>
                              <td><input v-model="item.amount_per_sqm" :id="costFocusId(group.key + '.' + item.key + '.amount_per_sqm')" :class="['field-input compact-input', costFocusClass(group.key + '.' + item.key + '.amount_per_sqm')]" :readonly="costItemAmountReadonly(item)" :title="costItemAmountReadonly(item) ? '由标准值及对应换算规则自动计算' : ''" @input="markCostItemEdited(item)" /></td>
                              <td>
                                <input v-model="item.source_note" :id="costFocusId(group.key + '.' + item.key + '.source_note')" :class="['field-input', costFocusClass(group.key + '.' + item.key + '.source_note')]" :readonly="costItemSourceReadonly(item)" @input="markCostItemEdited(item)" />
                                <small v-if="item.rule_key" class="muted-text">规则：{{ item.rule_key }}</small>
                              </td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                          <tfoot>
                            <tr :id="costFocusId('acquisition_items.ground_attachment')" :class="costFocusClass('acquisition_items.ground_attachment')">
                              <td colspan="5">土地取得费合计（试算）</td>
                              <td>{{ costLocalAcquisitionTotal || costAnalysis.totals?.acquisition_total || '待计算' }}</td>
                              <td colspan="2"><small class="muted-text">征地补偿 + 地上附着物补偿（建筑物、青苗，详见上方表3-1/3-2 折算）；点「计算并校核」后写入正式合计</small></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </section>
                    <section v-for="group in costPostAttachmentItemGroups" :id="'cost-section-tax'" :key="group.key" :class="['cost-item-group', 'cost-' + group.key]">
                      <header>
                        <div><strong>{{ group.label }}</strong><small>{{ costConfirmedCount(group.key) }} / {{ visibleCostItems(group.key).filter(item => item.enabled !== false).length }} 已确认；地区及政策匹配值修改后需重新确认。</small></div>
                        <button class="table-action" @click="confirmCostGroup(group.key)">全部确认</button>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>采用</th><th>项目</th><th>等别/口径</th><th>标准值</th><th>系数</th><th>金额（元/㎡）</th><th>依据/说明</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="item in visibleCostItems(group.key)" :key="item.key" :id="costFocusId(group.key + '.' + item.key)" :class="costFocusClass(group.key + '.' + item.key)">
                              <td><input type="checkbox" v-model="item.enabled" class="confirm-checkbox" @change="onCostItemEnabledChange(item)" /></td>
                              <td><input v-model="item.label" :id="costFocusId(group.key + '.' + item.key + '.label')" class="field-input" @input="markCostItemEdited(item)" /></td>
                              <td>
                                <select v-if="costGradeOptions(item).length" v-model="item.grade_name" :id="costFocusId(group.key + '.' + item.key + '.grade_name')" class="field-input compact-input" @change="onCostGradeChange(item)">
                                  <option value="">请选择</option>
                                  <option v-for="option in costGradeOptions(item)" :key="option" :value="option">{{ option }}</option>
                                </select>
                                <span v-else class="cost-na-chip">无</span>
                              </td>
                              <td><input v-model="item.standard_value" :id="costFocusId(group.key + '.' + item.key + '.standard_value')" class="field-input compact-input" :placeholder="costItemStandardPlaceholder(item)" @input="onCostItemValueInput(item)" /></td>
                              <td>
                                <div v-if="costItemUsesLandClassCoefficient(item)" class="cost-coefficient-cell">
                                  <input v-model="item.coefficient" :id="costFocusId(group.key + '.' + item.key + '.coefficient')" class="field-input compact-input" placeholder="地类修正系数" @input="onCostItemValueInput(item)" />
                                  <small class="muted-text">×0.0015 亩→㎡</small>
                                </div>
                                <input v-else-if="costItemUsesCoefficient(item)" v-model="item.coefficient" :id="costFocusId(group.key + '.' + item.key + '.coefficient')" class="field-input compact-input" placeholder="系数" @input="onCostItemValueInput(item)" />
                                <span v-else-if="costItemCoefficientHint(item)" class="cost-na-chip" :title="'0.0015 为元/亩折算元/平方米的固定单位换算系数'">{{ costItemCoefficientHint(item) }}</span>
                                <span v-else class="cost-na-chip">无独立系数</span>
                              </td>
                              <td><input v-model="item.amount_per_sqm" :id="costFocusId(group.key + '.' + item.key + '.amount_per_sqm')" class="field-input compact-input" :readonly="costItemAmountReadonly(item)" @input="markCostItemEdited(item)" /></td>
                              <td><input v-model="item.source_note" :id="costFocusId(group.key + '.' + item.key + '.source_note')" class="field-input" :readonly="costItemSourceReadonly(item)" @input="markCostItemEdited(item)" /></td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section v-if="costShowDevelopmentSurvey" class="cost-item-group cost-development-survey-group">
                      <header>
                        <div><strong>土地开发费项目调查包</strong><small>每份报告至少附3 组同区域、同开发程度的询价/预算/结算资料；系统展示调查均值与参考区间，不跨项目自动套用固定标准。</small></div>
                        <div class="cost-header-actions">
                          <button class="table-action" @click="addCostDevelopmentSurveyCase">新增案例</button>
                          <button class="table-action" @click="confirmCostDevelopmentSurveyCases">全部确认</button>
                        </div>
                      </header>
                      <div class="analysis-summary-strip">
                        <div :id="costFocusId('development_survey_analysis.average_total_per_sqm')" :class="costFocusClass('development_survey_analysis.average_total_per_sqm')"><span>调查均值</span><strong>{{ costDevelopmentSurveyAverage || '待计算' }}</strong><small>元/平方米</small></div>
                        <div :id="costFocusId('development_survey_analysis.valid_count')" :class="costFocusClass('development_survey_analysis.valid_count')"><span>有效案例</span><strong>{{ costAnalysis.development_survey_analysis?.valid_count || '0' }}</strong><small>已确认且可计算</small></div>
                        <div :id="costFocusId('development_survey_analysis.status')" :class="costFocusClass('development_survey_analysis.status')"><span>调查状态</span><strong>{{ costDevelopmentSurveyStatusLabel }}</strong><small>{{ costDevelopmentSurveyStatusHint }}</small></div>
                        <div :id="costFocusId('totals.development_total')" :class="costFocusClass('totals.development_total')"><span>本次采用合计</span><strong>{{ costAnalysis.totals?.development_total || '待计算' }}</strong><small>元/平方米</small></div>
                      </div>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>项目名称</th><th>位置</th><th>调查日期</th><th>资料类型</th><th>开发程度</th><th>开发费合计（元/㎡）</th><th>来源单位</th><th>备注</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="(item, index) in costAnalysis.development_survey_cases || []" :key="item.key || index">
                              <td><input v-model="item.name" :id="costFocusId('development_survey_cases.' + index + '.name')" class="field-input" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input v-model="item.location" :id="costFocusId('development_survey_cases.' + index + '.location')" class="field-input" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input v-model="item.survey_date" :id="costFocusId('development_survey_cases.' + index + '.survey_date')" class="field-input compact-input" placeholder="YYYY-MM-DD" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td>
                                <select v-model="item.source_type" :id="costFocusId('development_survey_cases.' + index + '.source_type')" class="field-input compact-input" @change="onCostDevelopmentSurveyInput(item)">
                                  <option value="">请选择</option>
                                  <option value="询价记录">询价记录</option>
                                  <option value="工程预算">工程预算</option>
                                  <option value="结算资料">结算资料</option>
                                </select>
                              </td>
                              <td><input v-model="item.development_set" :id="costFocusId('development_survey_cases.' + index + '.development_set')" class="field-input" :placeholder="form.land_development_set.value || '同本次设定开发程度'" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input v-model="item.total_per_sqm" :id="costFocusId('development_survey_cases.' + index + '.total_per_sqm')" class="field-input compact-input" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input v-model="item.source_unit" :id="costFocusId('development_survey_cases.' + index + '.source_unit')" class="field-input" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input v-model="item.note" :id="costFocusId('development_survey_cases.' + index + '.note')" class="field-input" @input="onCostDevelopmentSurveyInput(item)" /></td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section id="cost-section-development" class="cost-item-group cost-development-group">
                      <header>
                        <div><strong>土地开发费</strong><small>对应正文土地开发费分项表；参考区间为区域调查口径，本次采用值由估价师确认。</small></div>
                        <button class="table-action" @click="confirmCostGroup('development_items')">全部确认</button>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-development-table">
                          <thead><tr><th>土地开发项目</th><th>参考范围（元/㎡）</th><th>本次采用（元/㎡）</th><th>依据/说明</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="item in costAnalysis.development_items || []" :key="item.key">
                              <td><input v-model="item.label" :id="costFocusId('development_items.' + item.key + '.label')" class="field-input" @input="markCostItemEdited(item)" /></td>
                              <td><div class="cost-range-inputs"><input v-model="item.range_min" :id="costFocusId('development_items.' + item.key + '.range_min')" class="field-input compact-input" @input="markCostItemEdited(item)" /><span>至</span><input v-model="item.range_max" :id="costFocusId('development_items.' + item.key + '.range_max')" class="field-input compact-input" @input="markCostItemEdited(item)" /></div></td>
                              <td><input v-model="item.amount_per_sqm" :id="costFocusId('development_items.' + item.key + '.amount_per_sqm')" class="field-input compact-input" @input="markCostItemEdited(item)" /></td>
                              <td><input v-model="item.source_note" :id="costFocusId('development_items.' + item.key + '.source_note')" class="field-input" @input="markCostItemEdited(item)" /></td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                          <tfoot><tr><td>合计</td><td>/</td><td>{{ costAnalysis.totals?.development_total || '待计算' }}</td><td></td><td></td></tr></tfoot>
                        </table>
                      </div>
                    </section>
                  </section>

                  <section v-if="costWorkspaceView === 'adjustments'" id="focus_item_cost_approx_adjustments" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>年期、利润与区位修正</strong>
                      <label :id="costFocusId('development_cycle_years')" :class="costFocusClass('development_cycle_years')">开发周期（年）<input v-model="costAnalysis.development_cycle_years" :class="['field-input compact-input', costFocusClass('development_cycle_years')]" /></label>
                      <label :id="costFocusId('interest_rate')" :class="costFocusClass('interest_rate')">投资利息率（%）<input v-model="costAnalysis.interest_rate" :class="['field-input compact-input', costFocusClass('interest_rate')]" /></label>
                      <button class="table-action" @click="queryLatestLpr">查询最新LPR</button>
                      <button v-if="latestLpr" class="table-action" @click="applyLatestLpr">采用{{ latestLpr.one_year }}%</button>
                      <button class="icon-btn primary" @click="calculateCostApproximation">计算最终价格</button>
                    </div>
                    <div v-if="latestLpr" class="analysis-summary-strip">
                      <div><span>LPR来源</span><strong>{{ latestLpr.source }}</strong><small>{{ latestLpr.fetched ? '官网更新' : '本地PDF兜底' }}</small></div>
                      <div><span>发布日期</span><strong>{{ latestLpr.date }}</strong><small>用户确认后应用</small></div>
                      <div><span>1年期</span><strong>{{ latestLpr.one_year }}%</strong><small>投资利息率候选</small></div>
                      <div><span>5年期以上</span><strong>{{ latestLpr.five_year }}%</strong><small>仅供参考</small></div>
                    </div>
                    <details v-if="(costAnalysis.rounding_trace || []).length" id="focus_item_cost_approx_rounding_trace" class="cost-item-group">
                      <summary><strong>级联四舍五入轨迹</strong><small>正文、表格与 Word 共用已舍入中间结果</small></summary>
                      <ul class="cost-rounding-trace-list">
                        <li v-for="entry in costAnalysis.rounding_trace" :key="entry.key">
                          <span>{{ entry.label }}</span><strong>{{ entry.value }}</strong>
                        </li>
                      </ul>
                    </details>
                    <section class="cost-item-group">
                      <header>
                        <div><strong>分用途参数</strong><small>混合用途分别计算，不共用年期和增值收益率</small></div>
                        <button class="table-action" @click="confirmCostScenarios">全部确认</button>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>用途</th><th>使用年期</th><th>利润率</th><th>增值收益率%</th><th>安全利率%</th><th>土地还原率</th><th>区位修正率</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="scenario in costAnalysis.usage_scenarios || []" :key="scenario.key"
                                :id="costFocusId('usage_scenarios.' + scenario.key)"
                                :class="costFocusClass('usage_scenarios.' + scenario.key)">
                              <td><span class="cost-readonly-usage" :id="costFocusId('usage_scenarios.' + scenario.key + '.label')" :class="costFocusClass('usage_scenarios.' + scenario.key + '.label')">{{ scenario.label }}</span></td>
                              <td><input v-model="scenario.use_term_years" :id="costFocusId('usage_scenarios.' + scenario.key + '.use_term_years')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.use_term_years')]" /></td>
                              <td><input v-model="scenario.profit_rate" :id="costFocusId('usage_scenarios.' + scenario.key + '.profit_rate')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.profit_rate')]" /></td>
                              <td><input v-model="scenario.value_added_rate" :id="costFocusId('usage_scenarios.' + scenario.key + '.value_added_rate')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.value_added_rate')]" /></td>
                              <td><input v-model="scenario.safe_rate" :id="costFocusId('usage_scenarios.' + scenario.key + '.safe_rate')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.safe_rate')]" placeholder="可选" /></td>
                              <td><input v-model="scenario.reduction_rate" :id="costFocusId('usage_scenarios.' + scenario.key + '.reduction_rate')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.reduction_rate')]" /></td>
                              <td><input v-model="scenario.location_correction_rate" :id="costFocusId('usage_scenarios.' + scenario.key + '.location_correction_rate')" :class="['field-input compact-input', costFocusClass('usage_scenarios.' + scenario.key + '.location_correction_rate')]" /></td>
                              <td><input type="checkbox" v-model="scenario.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header>
                        <div><strong>土地还原率风险因素</strong><small>填写安全利率后，系统按“安全利率 + 风险调整值”派生土地还原率；无完整风险表时可直接确认用途场景中的土地还原率。</small></div>
                        <label>模式
                          <select v-model="costAnalysis.risk_mode" class="field-input" @change="onCostRiskModeChange">
                            <option value="direct">直接采用土地还原率</option>
                            <option value="analysis">风险分析</option>
                          </select>
                        </label>
                        <button v-if="costAnalysis.risk_mode === 'analysis'" class="table-action" @click="confirmCostRiskGroups">全部确认风险组</button>
                        <button v-if="costAnalysis.risk_mode === 'analysis'" class="table-action" @click="confirmCostRiskItems">全部确认因子</button>
                        <button v-if="costAnalysis.risk_mode === 'analysis'" class="table-action" @click="addCostRiskItem">新增风险因素</button>
                      </header>
                      <div v-if="costAnalysis.risk_mode !== 'analysis'" class="empty-hint">当前采用分用途参数表中的土地还原率；如需按风险因子推导，可切换为风险分析。</div>
                      <div v-if="costAnalysis.risk_mode === 'analysis'" class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>风险组</th><th>组权重</th><th>系统综合值</th><th>人工覆盖</th><th>采用值</th><th>覆盖依据</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="(group, index) in costAnalysis.risk_groups || []" :key="group.key || group.label"
                                :id="costFocusId('risk_groups.' + index)"
                                :class="costFocusClass('risk_groups.' + index)">
                              <td>{{ group.label }}</td>
                              <td><input v-model="group.weight" :id="costFocusId('risk_groups.' + index + '.weight')" :class="['field-input compact-input', costFocusClass('risk_groups.' + index + '.weight')]" @input="group.confirmed = false" /></td>
                              <td>{{ group.computed_value || '待校核' }}</td>
                              <td><input type="checkbox" v-model="group.override_enabled" class="confirm-checkbox" @change="group.confirmed = false" /></td>
                              <td><input v-model="group.override_value" :readonly="!group.override_enabled" :id="costFocusId('risk_groups.' + index + '.override_value')" :class="['field-input compact-input', costFocusClass('risk_groups.' + index + '.override_value')]" @input="group.confirmed = false" /></td>
                              <td><input v-model="group.override_reason" :readonly="!group.override_enabled" :id="costFocusId('risk_groups.' + index + '.override_reason')" :class="['field-input', costFocusClass('risk_groups.' + index + '.override_reason')]" @input="group.confirmed = false" /></td>
                              <td><input type="checkbox" v-model="group.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div v-if="costAnalysis.risk_mode === 'analysis'" class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>适用用途</th><th>风险组</th><th>组权重</th><th>风险因素</th><th>因素权重</th><th>风险等级</th><th>调整值</th><th>确认</th></tr></thead>
                          <tbody>
                            <tr v-for="(item, index) in costAnalysis.risk_items || []" :key="`${item.label}_${index}`"
                                :id="costFocusId('risk_items.' + index)"
                                :class="costFocusClass('risk_items.' + index)">
                              <td>
                                <select v-model="item.usage_key" :id="costFocusId('risk_items.' + index + '.usage_key')" :class="['field-input', costFocusClass('risk_items.' + index + '.usage_key')]">
                                  <option value="">全部用途</option>
                                  <option v-for="scenario in costAnalysis.usage_scenarios || []" :key="scenario.key" :value="scenario.key">{{ scenario.label }}</option>
                                </select>
                              </td>
                              <td><input v-model="item.group" :id="costFocusId('risk_items.' + index + '.group')" :class="['field-input', costFocusClass('risk_items.' + index + '.group')]" /></td>
                              <td><input v-model="item.group_weight" :id="costFocusId('risk_items.' + index + '.group_weight')" :class="['field-input compact-input', costFocusClass('risk_items.' + index + '.group_weight')]" /></td>
                              <td><input v-model="item.label" :id="costFocusId('risk_items.' + index + '.label')" :class="['field-input', costFocusClass('risk_items.' + index + '.label')]" /></td>
                              <td><input v-model="item.weight" :id="costFocusId('risk_items.' + index + '.weight')" :class="['field-input compact-input', costFocusClass('risk_items.' + index + '.weight')]" /></td>
                              <td>
                                <select v-model="item.level" :id="costFocusId('risk_items.' + index + '.level')" :class="['field-input compact-input', costFocusClass('risk_items.' + index + '.level')]" @change="onCostRiskLevelChange(item)">
                                  <option value="">待选择</option>
                                  <option v-for="option in costRiskLevelOptions(item)" :key="option.level" :value="option.level">{{ option.level }}</option>
                                </select>
                              </td>
                              <td><input v-model="item.adjustment_rate" :id="costFocusId('risk_items.' + index + '.adjustment_rate')" :class="['field-input compact-input', costFocusClass('risk_items.' + index + '.adjustment_rate')]" /></td>
                              <td><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header>
                        <div>
                          <strong>区位修正因素</strong>
                          <small v-if="costAnalysis.location_correction_mode === 'direct_sum'">住宅默认采用固定幅度等级修正：填写条件说明、选择优劣度并确认，系统自动计算修正率。</small>
                          <small v-else>高级模式保留外部 AHP 或人工综合修正结果。</small>
                        </div>
                        <label>修正方式
                          <select v-model="costAnalysis.location_correction_mode" class="field-input" @change="calculateCostApproximation">
                            <option value="direct_sum">固定幅度等级修正（推荐）</option>
                            <option value="advanced">高级因素分析</option>
                          </select>
                        </label>
                        <label>区位模板
                          <select v-model="costAnalysis.location_template_key" class="field-input" @change="onCostLocationTemplateChange">
                            <option v-for="option in costLocationTemplateOptions" :key="option.key" :value="option.key">{{ option.label }}</option>
                          </select>
                        </label>
                        <button class="table-action" @click="confirmCostLocationFactors">全部确认</button>
                        <button v-if="costDeletedTemplateLocationFactors.length" class="table-action" @click="restoreCostLocationFactors">恢复模板因素</button>
                        <label class="cost-inline-field">添加到因素组
                          <select v-model="costNewLocationFactorGroup" class="field-input compact-input">
                            <option v-for="group in costLocationFactorGroups" :key="group" :value="group">{{ group }}</option>
                          </select>
                        </label>
                        <button class="table-action" @click="addCostLocationFactor">新增因素</button>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>适用用途</th><th>因素组</th><th>因素</th><th>因素说明</th><th>{{ costAnalysis.location_correction_mode === 'direct_sum' ? '等级修正幅度%' : '权重' }}</th><th>优劣度</th><th>修正率</th><th>确认</th><th>操作</th></tr></thead>
                          <tbody>
                            <tr v-for="(factor, index) in costAnalysis.location_factors || []" :key="factor.key || `location_factor_${index}`"
                                :id="costFocusId('location_factors.' + index)"
                                :class="[costFocusClass('location_factors.' + index), { 'is-disabled-row': factor.enabled === false }]">
                              <td>
                                <select v-model="factor.usage_key" :id="costFocusId('location_factors.' + index + '.usage_key')" :class="['field-input', costFocusClass('location_factors.' + index + '.usage_key')]" :disabled="factor.enabled === false" @change="onCostLocationFactorChanged(factor)">
                                  <option value="">全部用途</option>
                                  <option v-for="scenario in costAnalysis.usage_scenarios || []" :key="scenario.key" :value="scenario.key">{{ scenario.label }}</option>
                                </select>
                              </td>
                              <td><input v-model="factor.group" :id="costFocusId('location_factors.' + index + '.group')" :class="['field-input', costFocusClass('location_factors.' + index + '.group')]" :disabled="factor.enabled === false" /></td>
                              <td><input v-model="factor.label" :id="costFocusId('location_factors.' + index + '.label')" :class="['field-input', costFocusClass('location_factors.' + index + '.label')]" :disabled="factor.enabled === false" /></td>
                              <td><input v-model="factor.description" :id="costFocusId('location_factors.' + index + '.description')" :class="['field-input', costFocusClass('location_factors.' + index + '.description')]" :disabled="factor.enabled === false" /></td>
                              <td><input v-if="costAnalysis.location_correction_mode === 'direct_sum'" v-model="factor.grade_amplitude" :id="costFocusId('location_factors.' + index + '.grade_amplitude')" :class="['field-input compact-input', costFocusClass('location_factors.' + index + '.grade_amplitude')]" :disabled="factor.enabled === false" @input="onCostLocationAmplitudeInput(factor)" /><input v-else v-model="factor.weight" :id="costFocusId('location_factors.' + index + '.weight')" :class="['field-input compact-input', costFocusClass('location_factors.' + index + '.weight')]" :disabled="factor.enabled === false" @input="onCostLocationFactorChanged(factor)" /></td>
                              <td>
                                <select v-if="costAnalysis.location_correction_mode === 'direct_sum'" v-model="factor.level" :id="costFocusId('location_factors.' + index + '.level')" :class="['field-input', costFocusClass('location_factors.' + index + '.level')]" :disabled="factor.enabled === false" @change="onCostLocationLevelChange(factor)">
                                  <option value="">待选择</option>
                                  <option v-for="level in costLocationLevels(factor)" :key="level" :value="level">{{ level }}</option>
                                </select>
                                <input v-else v-model="factor.level" :id="costFocusId('location_factors.' + index + '.level')" :class="['field-input compact-input', costFocusClass('location_factors.' + index + '.level')]" :disabled="factor.enabled === false" />
                              </td>
                              <td><input v-model="factor.correction_rate" :id="costFocusId('location_factors.' + index + '.correction_rate')" :class="['field-input compact-input', costFocusClass('location_factors.' + index + '.correction_rate')]" :readonly="costAnalysis.location_correction_mode === 'direct_sum'" :disabled="factor.enabled === false" @input="onCostLocationFactorChanged(factor, true)" /></td>
                              <td><input type="checkbox" v-model="factor.confirmed" class="confirm-checkbox" :disabled="factor.enabled === false" @change="onCostLocationFactorChanged(factor, false)" /></td>
                              <td>
                                <button v-if="factor.enabled === false" type="button" class="table-action compact-action" @click="restoreCostLocationFactor(factor)">恢复</button>
                                <button v-else type="button" class="table-action danger-action compact-action" @click="removeCostLocationFactor(factor, index)">删除</button>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>分用途计算结果</strong><small>计算结果只读；点击正文热区会定位到对应结果。</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table cost-result-table">
                          <thead><tr><th>用途</th><th>成本价格</th><th>投资利润</th><th>土地增值收益</th><th>年期修正系数</th><th>比准价格</th><th>区位修正率</th><th>最终单价</th></tr></thead>
                          <tbody>
                            <tr v-for="item in costAnalysis.usage_results || []" :key="item.key">
                              <td>{{ item.label }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.cost_price')" :class="costFocusClass('usage_results.' + item.key + '.cost_price')">{{ item.cost_price || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.profit')" :class="costFocusClass('usage_results.' + item.key + '.profit')">{{ item.profit || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.value_added_income')" :class="costFocusClass('usage_results.' + item.key + '.value_added_income')">{{ item.value_added_income || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.term_correction_factor')" :class="costFocusClass('usage_results.' + item.key + '.term_correction_factor')">{{ item.term_correction_factor || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.comparable_price')" :class="costFocusClass('usage_results.' + item.key + '.comparable_price')">{{ item.comparable_price || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.location_correction_rate')" :class="costFocusClass('usage_results.' + item.key + '.location_correction_rate')">{{ item.location_correction_rate || '待计算' }}</td>
                              <td :id="costFocusId('usage_results.' + item.key + '.final_price')" :class="costFocusClass('usage_results.' + item.key + '.final_price')">{{ item.final_price || '待计算' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                  </section>
                </template>

                <template v-if="activeProcessMethod.method_key === 'market_comp'">
                  <div class="market-workspace-tabs">
                    <button v-for="item in marketWorkspaceViews" :key="item.key"
                            :class="['icon-btn', { primary: marketWorkspaceView === item.key }]"
                            @click="marketWorkspaceView = item.key">
                      {{ item.label }}
                    </button>
                  </div>

                  <section v-show="marketWorkspaceView === 'instances'" :id="marketFocusId('selected_cases')" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>当前报告实例与计算参数</strong>
                      <label :id="marketFocusId('comparable_basis_status')" :class="marketFocusClass('comparable_basis_status')">价格可比基础
                        <select v-model="marketComparableBasisStatus" class="field-input compact-input" @change="onComparableBasisStatusChange">
                          <option value="consistent">口径一致，无需调整</option>
                          <option value="needs_adjustment">存在差异，需要修改正文</option>
                        </select>
                      </label>
                      <button class="icon-btn" @click="openComparableLibrary">前往实例库选取</button>
                      <button class="icon-btn primary" @click="calculateMarketComparison">计算比准地价</button>
                    </div>
                    <div class="analysis-summary-strip">
                      <div><span>A/B/C 已选</span><strong>{{ selectedComparableCount }} / 3</strong><small>最终实例在比较实例库选取</small></div>
                      <div><span>成交公告</span><strong>{{ marketEvidenceCount }} / 3</strong><small>用户上传官网截图</small></div>
                      <div><span>位置/现状</span><strong>{{ marketMapPhotoCount }} / 6</strong><small>位置图与现状图</small></div>
                      <div v-for="slot in comparableSlots" :key="`summary_${slot}`"
                           :id="marketFocusId('calculations.' + slot + '.correction_coefficient')"
                           :class="marketFocusClass('calculations.' + slot + '.correction_coefficient')"><span>实例 {{ slot }} 综合系数</span><strong>{{ marketCalculation(slot)?.correction_coefficient || '-' }}</strong><small :id="marketFocusId('calculations.' + slot + '.corrected_price')" :class="marketFocusClass('calculations.' + slot + '.corrected_price')">比准价{{ marketCalculation(slot)?.corrected_price || '-' }}</small></div>
                      <div :id="marketFocusId('market_comp_price')" :class="marketFocusClass('market_comp_price')"><span>最终单价</span><strong>{{ marketAnalysis?.market_comp_price || '-' }}</strong><small>元/㎡</small></div>
                    </div>
                    <div id="market-evidence-panel" :class="['market-evidence-panel', { complete: marketEvidenceCount === 3 }]">
                      <div>
                        <strong>比较实例 A/B/C 证据截图</strong>
                        <span>系统保留结构化数据用于测算；报告图片由估价师上传官网成交公告截图、位置图和现状图。</span>
                        <small>建议在中国土地市场网供地结果页检索电子监管号或项目名称，打开原页面后截图上传。</small>
                      </div>
                      <div class="comparable-actions">
                        <button v-for="slot in comparableSlots"
                                :key="`detail_${slot}`"
                                class="icon-btn"
                                @click="openLandChinaSupplyDetail(selectedComparableCase(slot))"
                                :disabled="!selectedComparableCase(slot) || !landChinaSupplyDetailUrl(selectedComparableCase(slot))">
                          打开实例 {{ slot }} 详情
                        </button>
                      </div>
                    </div>
                    <div class="market-evidence-upload-grid">
                      <section v-for="slot in comparableSlots" :key="`evidence_${slot}`" class="market-evidence-card">
                        <header>
                          <div>
                            <strong>实例 {{ slot }}</strong>
                            <small>{{ selectedComparableCase(slot)?.project_name || '未选择实例' }}</small>
                          </div>
                          <div class="slot-actions">
                            <button class="table-action" @click="copyComparableEvidenceKeyword(slot)" :disabled="!selectedComparableCase(slot)">复制检索词</button>
                          </div>
                        </header>
                        <p>{{ comparableEvidenceKeyword(slot) || '请先在比较实例库选取实例。' }}</p>
                        <div class="market-evidence-kind-row" v-for="kind in marketEvidenceKinds" :key="`${slot}_${kind.key}`">
                          <div>
                            <strong>{{ kind.label }}</strong>
                            <small>{{ evidenceSnapshotFor(slot, kind.key)?.image_paths?.length ? '已上传' : kind.help }}</small>
                          </div>
                          <input type="file"
                                 accept="image/*"
                                 multiple
                                 :disabled="!selectedComparableCase(slot)"
                                 @change="handleComparableEvidenceUpload(slot, kind.key, $event)" />
                        </div>
                      </section>
                    </div>
                    <div class="selected-case-grid">
                      <div v-for="(slot, index) in comparableSlots" :key="slot"
                           :id="marketFocusId('selected_cases.' + index)"
                           :class="marketFocusClass('selected_cases.' + index)">
                        <strong>实例 {{ slot }}</strong>
                        <span :id="marketFocusId('selected_cases.' + index + '.electronic_supervision_no')" :class="marketFocusClass('selected_cases.' + index + '.electronic_supervision_no')">{{ selectedComparableCase(slot)?.electronic_supervision_no || '未选择' }}</span>
                        <small :id="marketFocusId('selected_cases.' + index + '.project_name')" :class="marketFocusClass('selected_cases.' + index + '.project_name')">{{ selectedComparableCase(slot)?.project_name || '' }}</small>
                        <small :id="marketFocusId('selected_cases.' + index + '.location')" :class="marketFocusClass('selected_cases.' + index + '.location')">{{ selectedComparableCase(slot)?.location || '' }}</small>
                        <small v-if="selectedComparableCase(slot)">
                          合同签订：<span :id="marketFocusId('selected_cases.' + index + '.transaction_date')" :class="marketFocusClass('selected_cases.' + index + '.transaction_date')">{{ selectedComparableCase(slot)?.transaction_date || '-' }}</span>；
                          成交价：<span :id="marketFocusId('selected_cases.' + index + '.total_price_wan')" :class="marketFocusClass('selected_cases.' + index + '.total_price_wan')">{{ selectedComparableCase(slot)?.total_price_wan || '-' }}</span>万元；
                          单价：<span :id="marketFocusId('selected_cases.' + index + '.unit_price_sqm')" :class="marketFocusClass('selected_cases.' + index + '.unit_price_sqm')">{{ selectedComparableCase(slot)?.unit_price_sqm || '-' }}</span>元/㎡
                        </small>
                      </div>
                    </div>
                  </section>

                  <section v-show="marketWorkspaceView === 'factors'" id="focus_item_market_comp_factors" class="market-workspace-panel">
                    <div class="market-scheme-source-bar">
                      <div>
                        <span>当前报告规则来源</span>
                        <strong>{{ marketSchemeName }}</strong>
                        <small>当前报告使用冻结规则快照；全局规则修改不会静默改动本报告。</small>
                      </div>
                      <button class="table-action" @click="openRuleManagement">前往规则管理</button>
                    </div>
                    <div class="market-factor-toolbar">
                      <div><strong>因素确认进度 {{ marketAnalysisSummary.percent }}%</strong><span>{{ marketAnalysisSummary.confirmed }} / {{ marketAnalysisSummary.total }} 项实例因素已确认</span></div>
                      <div class="market-factor-filter">
                        <button :class="['table-action', { active: marketFactorFilter === 'all' }]" @click="marketFactorFilter = 'all'">全部</button>
                        <button :class="['table-action', { active: marketFactorFilter === 'pending' }]" @click="marketFactorFilter = 'pending'">仅待确认</button>
                      </div>
                    </div>
                    <div v-if="!marketAnalysis?.factors?.length" class="process-empty">
                      请先在“实例与参数”中选择三宗实例并计算，系统才会生成因素确认任务。
                    </div>
                    <section v-for="(factors, group) in visibleMarketFactorGroups" :key="group" class="market-factor-group">
                      <h3>{{ group }} <span>{{ factors.length }} 项</span></h3>
                      <button v-for="factor in factors" :key="factor.key"
                              :id="marketFocusId('factors.' + factor.key)"
                              :class="['market-factor-task', factorConfirmedCount(factor) === comparableSlots.length ? 'factor-state-confirmed' : 'factor-state-pending', marketFocusClass('factors.' + factor.key)]"
                              @click="openFactorGuide(factor)">
                        <span class="market-factor-task-main">
                          <strong>{{ factor.label }}</strong>
                          <small>
                            {{ factor.required ? '必填' : '可选' }} ·
                            {{ factorConfirmedCount(factor) === comparableSlots.length ? '本报告已校核' : (factor.review_status === 'confirmed' ? '规则已校核' : '规则模板待校核') }} ·
                            {{ factorSourceLabel(factor.source) }}
                          </small>
                        </span>
                        <span class="market-factor-task-progress">{{ factorConfirmedCount(factor) }} / 3 已确认</span>
                        <span v-if="factorMissingIndexCount(factor)" class="market-factor-task-warning">缺少 {{ factorMissingIndexCount(factor) }} 个指数</span>
                        <span class="market-factor-task-action">判定条件</span>
                      </button>
                    </section>
                  </section>
                </template>

                <template v-if="activeProcessMethod.method_key === 'income_cap'">
                  <div class="market-workspace-tabs">
                    <button v-for="item in incomeWorkspaceViews" :key="item.key"
                            :class="['icon-btn', { primary: incomeWorkspaceView === item.key }]"
                            @click="incomeWorkspaceView = item.key">
                      {{ item.label }}
                    </button>
                  </div>

                  <section v-show="incomeWorkspaceView === 'instances'" id="focus_item_income_cap_analysis" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>估价对象房屋、宗地与租金实例</strong>
                      <span>先核对估价对象事实与评估设定，再录入收益还原法独立租金实例及图片证据。</span>
                      <button class="icon-btn primary" @click="calculateIncomeCapitalization">计算收益还原法</button>
                    </div>
                    <div class="analysis-summary-strip">
                      <div><span>有效租金实例</span><strong>{{ incomeRentInstanceCount }} / 3</strong><small>A/B/C 必须固定</small></div>
                      <div><span>图片资料</span><strong>{{ incomeImageCount }} / 6</strong><small>照片与位置图</small></div>
                      <div><span>平均月租金</span><strong>{{ incomeAnalysis.income_results?.average_monthly_rent || '-' }}</strong><small>元/㎡·月</small></div>
                      <div><span>收益法单价</span><strong>{{ incomeAnalysis.income_cap_price || '-' }}</strong><small>元/㎡</small></div>
                    </div>
                    <section class="cost-item-group">
                      <header><div><strong>估价对象房屋情况</strong><small>录入现场勘察确认的房屋事实，用于租金判断、折旧和房屋现值测算。</small></div></header>
                      
                      <!-- 中间值实时可视化看板 -->
                      <div class="income-analysis-dashboard">
                        <div :id="incomeFocusId('income_results.building_replacement_price')" :class="['dashboard-card', incomeFocusClass('income_results.building_replacement_price')]">
                          <span>房屋重置总价</span>
                          <strong>{{ incomeAnalysis.income_results?.building_replacement_price || '-' }}<small>万元</small></strong>
                        </div>
                        <div :id="incomeFocusId('income_results.annual_depreciation')" :class="['dashboard-card', incomeFocusClass('income_results.annual_depreciation')]">
                          <span>年折旧费</span>
                          <strong>{{ incomeAnalysis.income_results?.annual_depreciation || '-' }}<small>万元</small></strong>
                        </div>
                        <div :id="incomeFocusId('income_results.building_current_value')" :class="['dashboard-card', incomeFocusClass('income_results.building_current_value')]">
                          <span>房屋现值</span>
                          <strong>{{ incomeAnalysis.income_results?.building_current_value || '-' }}<small>万元</small></strong>
                        </div>
                        <div :id="incomeFocusId('income_results.average_monthly_rent')" :class="['dashboard-card', incomeFocusClass('income_results.average_monthly_rent')]">
                          <span>平均月租金</span>
                          <strong>{{ incomeAnalysis.income_results?.average_monthly_rent || '-' }}<small>元/㎡·月</small></strong>
                        </div>
                      </div>

                      <div class="income-profile-sub-title">1. 基本信息与现状利用</div>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('building_profile.building_location')" :class="incomeFocusClass('building_profile.building_location')">房屋坐落<input v-model="incomeAnalysis.building_profile.building_location" class="field-input" /></label>
                        <label :id="incomeFocusId('building_profile.building_form')" :class="incomeFocusClass('building_profile.building_form')">建筑物形态input v-model="incomeAnalysis.building_profile.building_form" class="field-input" placeholder="如：独栋建筑物 /></label>
                        <label :id="incomeFocusId('building_profile.actual_use')" :class="incomeFocusClass('building_profile.actual_use')">地上房屋实际用途input v-model="incomeAnalysis.building_profile.actual_use" class="field-input" placeholder="如：住宅" /></label>
                        <label :id="incomeFocusId('building_profile.built_year')" :class="incomeFocusClass('building_profile.built_year')">建成年份<input v-model="incomeAnalysis.building_profile.built_year" class="field-input compact-input" @input="syncIncomeBuildingYears('built_year')" /></label>
                        <label :id="incomeFocusId('building_profile.floor_desc')" :class="incomeFocusClass('building_profile.floor_desc')">总层数input v-model="incomeAnalysis.building_profile.floor_desc" class="field-input" placeholder="如：4" /></label>
                        <label :id="incomeFocusId('building_profile.owner_floor_desc')" :class="incomeFocusClass('building_profile.owner_floor_desc')">业主房屋所在层数input v-model="incomeAnalysis.building_profile.owner_floor_desc" class="field-input" placeholder="如：1-4" /></label>
                      </div>

                      <div class="income-profile-sub-title">2. 建筑结构与装饰装修</div>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('building_profile.structure')" :class="incomeFocusClass('building_profile.structure')">建筑结构
                          <select v-model="incomeAnalysis.building_profile.structure" class="field-input compact-input" @change="onIncomeStructureChange">
                            <option v-for="option in residentialStructureOptions" :key="option.key" :value="option.label">{{ option.label }}</option>
                          </select>
                        </label>
                        <label :id="incomeFocusId('building_profile.exterior')" :class="incomeFocusClass('building_profile.exterior')">外墙情况<input v-model="incomeAnalysis.building_profile.exterior" class="field-input" placeholder="如：双飞粉" /></label>
                        <label :id="incomeFocusId('building_profile.entrance_door')" :class="incomeFocusClass('building_profile.entrance_door')">入户门<input v-model="incomeAnalysis.building_profile.entrance_door" class="field-input" placeholder="如：不锈钢及木质" /></label>
                        <label :id="incomeFocusId('building_profile.windows')" :class="incomeFocusClass('building_profile.windows')">窗户<input v-model="incomeAnalysis.building_profile.windows" class="field-input" placeholder="如：塑钢" /></label>
                        <label :id="incomeFocusId('building_profile.security_facilities')" :class="incomeFocusClass('building_profile.security_facilities')">防盗设施<input v-model="incomeAnalysis.building_profile.security_facilities" class="field-input" placeholder="如：铁艺；无则填无" /></label>
                        <label :id="incomeFocusId('building_profile.floor_finish')" :class="incomeFocusClass('building_profile.floor_finish')">地面情况<input v-model="incomeAnalysis.building_profile.floor_finish" class="field-input" placeholder="如：地贴瓷砖" /></label>
                        <label :id="incomeFocusId('building_profile.ceiling_finish')" :class="incomeFocusClass('building_profile.ceiling_finish')">顶棚<input v-model="incomeAnalysis.building_profile.ceiling_finish" class="field-input" placeholder="如：木质装饰吊顶" /></label>
                        <label :id="incomeFocusId('building_profile.interior')" :class="incomeFocusClass('building_profile.interior')">装修情况<input v-model="incomeAnalysis.building_profile.interior" class="field-input compact-input" /></label>
                      </div>

                      <div class="income-profile-sub-title">3. 维护成新与耐用年限</div>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('building_profile.maintenance')" :class="incomeFocusClass('building_profile.maintenance')">维护保养状况<input v-model="incomeAnalysis.building_profile.maintenance" class="field-input" placeholder="如：一般" /></label>
                        <label :id="incomeFocusId('building_profile.newness_desc')" :class="incomeFocusClass('building_profile.newness_desc')">成新度描述<input v-model="incomeAnalysis.building_profile.newness_desc" class="field-input compact-input" placeholder="如：七成新" /></label>
                        <label :id="incomeFocusId('building_profile.newness_rate')" :class="incomeFocusClass('building_profile.newness_rate')">成新率（%）<input v-model="incomeAnalysis.building_profile.newness_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('building_profile.economic_life_years')" :class="incomeFocusClass('building_profile.economic_life_years')">经济耐用年限<input v-model="incomeAnalysis.building_profile.economic_life_years" class="field-input compact-input" @input="syncIncomeBuildingYears('economic_life_years')" /></label>
                        <label :id="incomeFocusId('building_profile.used_years')" :class="incomeFocusClass('building_profile.used_years')">已使用年限<input v-model="incomeAnalysis.building_profile.used_years" class="field-input compact-input" @input="syncIncomeBuildingYears('used_years')" /></label>
                        <label :id="incomeFocusId('building_profile.remaining_years')" :class="incomeFocusClass('building_profile.remaining_years')">剩余年限<input v-model="incomeAnalysis.building_profile.remaining_years" class="field-input compact-input" @input="syncIncomeBuildingYears('remaining_years')" /></label>
                      </div>
                    </section>

                    <section class="cost-item-group">
                      <header><div><strong>宗地指标与评估设定</strong><small>区分资料记载的面积、现状容积率与本次评估采用的设定条件。</small></div></header>
                      <div class="income-profile-sub-title">4. 面积、容积率及资料依据</div>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('building_profile.building_area')" :class="incomeFocusClass('building_profile.building_area')">建筑面积（㎡）input v-model="incomeAnalysis.building_profile.building_area" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('building_profile.building_area_basis')" :class="incomeFocusClass('building_profile.building_area_basis')">建筑面积依据
                          <input v-model="incomeAnalysis.building_profile.building_area_basis" class="field-input" placeholder="可手填或引用已有依据" />
                          <span class="basis-reference-actions"><select class="field-input" @change="e => { setIncomeBasisReference('building_area_basis', e.target.value); e.target.value = '' }"><option value="">引用已有依据</option><option v-for="option in sharedBasisReferenceOptions" :key="`income_build_${option}`" :value="option">{{ option }}</option></select><button class="table-action inline-mini" @click="addSharedValuationBasis(incomeAnalysis.building_profile.building_area_basis)">加入共享清单</button></span>
                        </label>
                        <label :id="incomeFocusId('building_profile.land_area')" :class="incomeFocusClass('building_profile.land_area')">土地面积（㎡）input v-model="incomeAnalysis.building_profile.land_area" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('building_profile.land_area_basis')" :class="incomeFocusClass('building_profile.land_area_basis')">土地面积依据
                          <input v-model="incomeAnalysis.building_profile.land_area_basis" class="field-input" placeholder="可手填或引用已有依据" />
                          <span class="basis-reference-actions"><select class="field-input" @change="e => { setIncomeBasisReference('land_area_basis', e.target.value); e.target.value = '' }"><option value="">引用已有依据</option><option v-for="option in sharedBasisReferenceOptions" :key="`income_land_${option}`" :value="option">{{ option }}</option></select><button class="table-action inline-mini" @click="addSharedValuationBasis(incomeAnalysis.building_profile.land_area_basis)">加入共享清单</button></span>
                        </label>
                      </div>

                      <div class="income-profile-sub-title">5. 本次评估设定</div>
                      <div class="income-part2-reference-strip">
                        <button type="button" class="income-reference-card" @click="scrollToField('set_plot_ratio')"><span>引用第二部分设定容积率</span><strong>{{ form.set_plot_ratio_display?.value || form.set_plot_ratio?.value || '待填写' }}</strong></button>
                        <button type="button" class="income-reference-card" @click="scrollToField('valuation_condition_type')"><span>引用第二部分利用条件类型</span><strong>{{ derivedUseCondition() || '待填写' }}</strong></button>
                      </div>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('building_profile.current_use_basis')" :class="incomeFocusClass('building_profile.current_use_basis')">评估设定依据
                          <input v-model="incomeAnalysis.building_profile.current_use_basis" class="field-input" placeholder="可手填或引用已有依据" />
                          <span class="basis-reference-actions"><select class="field-input" @change="e => { setIncomeBasisReference('current_use_basis', e.target.value); e.target.value = '' }"><option value="">引用已有依据</option><option v-for="option in sharedBasisReferenceOptions" :key="`income_condition_${option}`" :value="option">{{ option }}</option></select><button class="table-action inline-mini" @click="addSharedValuationBasis(incomeAnalysis.building_profile.current_use_basis)">加入共享清单</button></span>
                        </label>
                      </div>
                    </section>

                    <section class="cost-item-group income-rent-instance-section">
                      <header>
                        <div>
                          <strong>租金比较实例 A/B/C</strong>
                          <small>本页录入实例基本事实与图片证据；区位及个别因素统一在“租金因素确认”中校核。</small>
                        </div>
                      </header>
                      <div class="market-evidence-upload-grid">
                      <section v-for="(item, index) in incomeAnalysis.rent_instances || []" :key="item.slot"
                               :class="['market-evidence-card', { 'rent-instance-card-confirmed': item.confirmed }]">
                        <header>
                          <div>
                            <strong>租金实例 {{ item.slot }}</strong>
                            <small>{{ item.name || '待录入实例名称' }}</small>
                          </div>
                          <label class="income-confirm"><input type="checkbox" v-model="item.confirmed" class="confirm-checkbox" /> 确认采用</label>
                        </header>
                        <div class="income-instance-fields">
                          <label :id="incomeFocusId(`rent_instances.${item.slot}.name`)" :class="incomeFocusClass(`rent_instances.${item.slot}.name`)">实例名称<input v-model="item.name" class="field-input" /></label>
                          <label :id="incomeFocusId(`rent_instances.${item.slot}.location`)" :class="incomeFocusClass(`rent_instances.${item.slot}.location`)">实例坐落<input v-model="item.location" class="field-input" /></label>
                          <label :id="incomeFocusId(`rent_instances.${item.slot}.usage_key`)" :class="incomeFocusClass(`rent_instances.${item.slot}.usage_key`)">出租物业用途
                            <select v-model="item.usage_key" class="field-input" @change="onRentUsageChange(item)">
                              <option v-for="option in rentalUsageOptions" :key="`${item.slot}_${option.key}`" :value="option.key">{{ option.label }}</option>
                            </select>
                          </label>
                          <label v-if="item.usage_key === 'other'" :id="incomeFocusId(`rent_instances.${item.slot}.usage_other`)" :class="incomeFocusClass(`rent_instances.${item.slot}.usage_other`)">其他用途<input v-model="item.usage_other" class="field-input" @input="onRentUsageChange(item)" /></label>
                          <label :id="incomeFocusId(`rent_instances.${item.slot}.monthly_rent`)" :class="incomeFocusClass(`rent_instances.${item.slot}.monthly_rent`)">月租金（元/㎡·月）<input v-model="item.monthly_rent" class="field-input" /></label>
                          <label :id="incomeFocusId(`rent_instances.${item.slot}.transaction_date`)" :class="incomeFocusClass(`rent_instances.${item.slot}.transaction_date`)">租金调查时点<input v-model="item.transaction_date" class="field-input" @input="onRentTransactionDateChange(item)" /></label>
                        </div>
                        <div class="income-instance-media-grid">
                        <div class="upload-preview-container">
                          <span class="upload-title">实例照片</span>
                          <input :id="`income-file-${index}-photo`" type="file" accept="image/*" class="hidden-file-input" @change="handleIncomeImageUpload(index, 'photo', $event)" />
                          <div v-if="!item.photo_data" class="upload-placeholder" @click="triggerIncomeImageUpload(index, 'photo')">
                            <span class="upload-icon">+</span>
                            <span>上传租赁实例照片</span>
                          </div>
                          <div v-else class="image-thumb-wrapper" :title="item.photo_name || '双击或点击重新上传'">
                            <img :src="item.photo_data" class="image-thumb" alt="照片预览" />
                            <div class="image-thumb-overlay">
                              <button class="table-action" @click="triggerIncomeImageUpload(index, 'photo')">重传</button>
                              <button class="table-action danger" @click.stop="removeIncomeImage(index, 'photo')">删除</button>
                            </div>
                          </div>
                        </div>
                        <div class="upload-preview-container">
                          <span class="upload-title">位置图</span>
                          <input :id="`income-file-${index}-location`" type="file" accept="image/*" class="hidden-file-input" @change="handleIncomeImageUpload(index, 'location', $event)" />
                          <div v-if="!item.location_image_data" class="upload-placeholder" @click="triggerIncomeImageUpload(index, 'location')">
                            <span class="upload-icon">+</span>
                            <span>上传实例位置截图</span>
                          </div>
                          <div v-else class="image-thumb-wrapper" :title="item.location_image_name || '双击或点击重新上传'">
                            <img :src="item.location_image_data" class="image-thumb" alt="位置预览" />
                            <div class="image-thumb-overlay">
                              <button class="table-action" @click="triggerIncomeImageUpload(index, 'location')">重传</button>
                              <button class="table-action danger" @click.stop="removeIncomeImage(index, 'location')">删除</button>
                            </div>
                          </div>
                        </div>
                        </div>
                      </section>
                      </div>
                    </section>
                  </section>

                  <section v-show="incomeWorkspaceView === 'factors'" id="focus_item_income_cap_factors" class="market-workspace-panel">
                    <div class="market-factor-toolbar-container">
                      <div class="market-factor-toolbar-top">
                        <div class="factor-progress-info">
                          <strong>租金因素确认进度 {{ incomeFactorSummary.percent }}%</strong>
                          <span>{{ incomeFactorSummary.confirmed }} / {{ incomeFactorSummary.total }} 项实例因素已确认</span>
                        </div>
                        <div class="factor-action-buttons">
                          <button class="table-action confirmed" @click="confirmAllIncomeFactors">全部确认</button>
                          <button class="table-action danger-light" @click="cancelAllIncomeFactors">全部取消确认</button>
                          <button class="icon-btn primary compact-btn" @click="calculateIncomeCapitalization">重新计算租金</button>
                        </div>
                      </div>
                      <div class="market-factor-toolbar-bottom">
                        <div class="market-segmented-tabs">
                          <button :class="['segmented-tab-btn', { active: incomeFactorFilter === 'all' }]" @click="incomeFactorFilter = 'all'">全部</button>
                          <button :class="['segmented-tab-btn', { active: incomeFactorFilter === '交易因素' }]" @click="incomeFactorFilter = '交易因素'">交易</button>
                          <button :class="['segmented-tab-btn', { active: incomeFactorFilter === '区域因素' }]" @click="incomeFactorFilter = '区域因素'">区域</button>
                          <button :class="['segmented-tab-btn', { active: incomeFactorFilter === '个别因素' }]" @click="incomeFactorFilter = '个别因素'">个别</button>
                        </div>
                      </div>
                    </div>
                    <section v-for="(factors, group) in visibleIncomeFactorGroups" :key="group" class="market-factor-group">
                      <h3>{{ group }} <span>{{ factors.length }} 项</span></h3>
                      <div v-for="factor in factors" :key="factor.key"
                           :id="incomeFocusId('rent_factor_items.' + factor.key)"
                           :class="['income-factor-card', { 'factor-card-collapsed': isFactorConfirmed(factor) && !factor.tempExpanded }]">
                        <header @click="isFactorConfirmed(factor) ? factor.tempExpanded = !factor.tempExpanded : null" :style="{ cursor: isFactorConfirmed(factor) ? 'pointer' : 'default' }">
                          <div>
                            <strong>{{ factor.label }}</strong>
                            <small>{{ factor.help_text }}</small>
                            <span v-if="isFactorConfirmed(factor)" class="badge-confirmed" style="margin-left: 8px; color: var(--color-morandi-green-strong); font-weight: bold;">
                              已确认
                            </span>
                            <span v-if="isFactorConfirmed(factor) && !factor.tempExpanded" class="badge-collapsed-preview" style="margin-left: 8px; font-size: 0.85rem; color: var(--text-muted);">
                              （已折叠；案例 A：{{ factor.cases?.A?.index || '-' }}，B：{{ factor.cases?.B?.index || '-' }}，C：{{ factor.cases?.C?.index || '-' }}）
                            </span>
                          </div>
                          <button :class="['table-action', { confirmed: isFactorConfirmed(factor) }]" @click.stop="toggleFactorConfirm(factor)">
                            {{ isFactorConfirmed(factor) ? '已确认' : '确认该因素' }}
                          </button>
                        </header>
                        <div v-show="!isFactorConfirmed(factor) || factor.tempExpanded" class="table-scroll">
                          <table class="comparable-table cost-edit-table income-factor-table">
                            <thead><tr><th>对象</th><th>来源</th><th>条件</th><th>指数</th><th>修正状态</th><th>确认</th></tr></thead>
                            <tbody>
                              <tr>
                                <td>估价对象</td>
                                <td><span class="factor-source-chip">第二部分/本报告</span></td>
                                <td>
                                  <select v-if="factor.levels?.length" v-model="factor.subject_level_label" class="field-input" :disabled="factor.key === 'transaction_condition'" @change="applyIncomeSubjectLevel(factor)">
                                    <option value="">选择估价对象条件</option>
                                    <option v-for="level in factor.levels || []" :key="`${factor.key}_subject_${level.label}`" :value="level.label">{{ level.label }}</option>
                                  </select>
                                  <input v-else v-model="factor.subject_value" class="field-input" @input="markIncomeFactorSubjectEdited(factor)" />
                                </td>
                                <td><input value="100.00" class="field-input compact-input" readonly /></td>
                                <td>基准</td>
                                <td>—</td>
                              </tr>
                              <tr v-for="slot in comparableSlots" :key="`${factor.key}_${slot}`"
                                  :id="incomeFocusId('rent_factor_items.' + factor.key + '.cases.' + slot + '.value')"
                                  :class="incomeFocusClass('rent_factor_items.' + factor.key + '.cases.' + slot + '.value')">
                                <td>案例{{ slot }}</td>
                                <td>
                                  <span class="factor-source-chip">{{ incomeFactorSourceLabel(factor.cases[slot].source) }}</span>
                                  <button v-if="factor.cases[slot].source === 'manual_override' && ['usage', 'transaction_time'].includes(factor.key)" class="table-action inline-mini" @click="restoreIncomeFactorInstanceReference(factor, slot)">恢复实例引用</button>
                                </td>
                                <td>
                                  <select v-if="factor.levels?.length" v-model="factor.cases[slot].level_label" class="field-input" @change="applyIncomeFactorLevel(factor, slot)"><option value="">选择条件</option><option v-for="level in factor.levels || []" :key="`${factor.key}_${slot}_${level.label}`" :value="level.label">{{ level.label }}</option></select>
                                  <input v-else v-model="factor.cases[slot].value" class="field-input" @input="markIncomeFactorCaseEdited(factor, slot)" />
                                  <input v-if="factor.key === 'transaction_condition' && normalizeIncomeFactorValue(factor.key, factor.cases[slot].value) === '非正常交易'"
                                         v-model="factor.cases[slot].override_reason"
                                         class="field-input factor-adjustment-reason"
                                         placeholder="填写非正常交易情况及人工调整依据"
                                         @input="factor.cases[slot].source = 'manual_override'; factor.cases[slot].confirmed = false" />
                                </td>
                                <td><input v-model="factor.cases[slot].index"
                                           class="field-input compact-input"
                                           :readonly="factor.key === 'transaction_condition' && normalizeIncomeFactorValue(factor.key, factor.cases[slot].value) === '正常交易'"
                                           :placeholder="factor.key === 'transaction_condition' && normalizeIncomeFactorValue(factor.key, factor.cases[slot].value) === '非正常交易' ? '人工填写指数' : ''"
                                           @input="factor.cases[slot].source = 'manual_override'; factor.cases[slot].confirmed = false" /></td>
                                <td><span :class="incomeFactorCaseStatusClass(factor, slot)">{{ incomeFactorCaseStatus(factor, slot) }}</span></td>
                                <td><input type="checkbox" v-model="factor.cases[slot].confirmed" class="confirm-checkbox" /></td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </section>
                  </section>

                  <section v-show="incomeWorkspaceView === 'parameters'" id="focus_item_income_cap_parameters" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>收入费用与还原率参数</strong>
                      <button class="table-action" @click="confirmIncomeCapRates">确认还原率</button>
                      <button class="icon-btn primary" @click="calculateIncomeCapitalization">计算收益还原法</button>
                    </div>
                    <section class="cost-item-group">
                      <header><div><strong>收入参数</strong><small>影响房地年总收益。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('income_parameters.vacancy_rate_range')" :class="incomeFocusClass('income_parameters.vacancy_rate_range')">区域平均空置率区间input v-model="incomeAnalysis.income_parameters.vacancy_rate_range" class="field-input" placeholder="如：3%-5%" /></label>
                        <label :id="incomeFocusId('income_parameters.vacancy_rate')" :class="incomeFocusClass('income_parameters.vacancy_rate')">本次采用空置率<input v-model="incomeAnalysis.income_parameters.vacancy_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('income_parameters.rentable_area_ratio')" :class="incomeFocusClass('income_parameters.rentable_area_ratio')">有效出租面积比率%<input v-model="incomeAnalysis.income_parameters.rentable_area_ratio" class="field-input compact-input" /></label>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>费用与房屋现值参数</strong><small>按范本拆分管理费、维修费、保险费和税金。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('expense_parameters.management_rate')" :class="incomeFocusClass('expense_parameters.management_rate')">管理费率%<input v-model="incomeAnalysis.expense_parameters.management_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.repair_rate')" :class="incomeFocusClass('expense_parameters.repair_rate')">维修费率%<input v-model="incomeAnalysis.expense_parameters.repair_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.replacement_cost_grade_key')" :class="incomeFocusClass('expense_parameters.replacement_cost_grade_key')">住宅结构等级
                          <select v-model="incomeAnalysis.expense_parameters.replacement_cost_grade_key" class="field-input compact-input" @change="onIncomeCostGradeChange">
                            <option v-for="option in incomeCostGradeOptions" :key="option.key" :value="option.gradeKey">{{ option.grade === '/' ? option.structure : `${option.structure}${option.grade}` }}</option>
                          </select>
                        </label>
                        <label :id="incomeFocusId('expense_parameters.replacement_cost_range_max')" :class="incomeFocusClass('expense_parameters.replacement_cost_range_max')">文件取价范围
                          <input :value="`${incomeAnalysis.expense_parameters.replacement_cost_range_min || selectedIncomeCostStandard.min}-${incomeAnalysis.expense_parameters.replacement_cost_range_max || selectedIncomeCostStandard.max}`" class="field-input compact-input" readonly />
                        </label>
                        <label :id="incomeFocusId('expense_parameters.replacement_base_unit_cost')" :class="incomeFocusClass('expense_parameters.replacement_base_unit_cost')">本次采用建设成本单价
                          <input v-model="incomeAnalysis.expense_parameters.replacement_base_unit_cost" class="field-input compact-input" @input="markIncomeReplacementCostManual" />
                          <button type="button" class="table-action inline-mini" @click="resetIncomeReplacementCostToRangeMax">恢复上限</button>
                        </label>
                        <label :id="incomeFocusId('expense_parameters.regional_adjustment_coefficient')" :class="incomeFocusClass('expense_parameters.regional_adjustment_coefficient')">地区系数<input v-model="incomeAnalysis.expense_parameters.regional_adjustment_coefficient" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.cost_growth_rate')" :class="incomeFocusClass('expense_parameters.cost_growth_rate')">增长率<input v-model="incomeAnalysis.expense_parameters.cost_growth_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.cost_base_date')" :class="incomeFocusClass('expense_parameters.cost_base_date')">成本基准日input v-model="incomeAnalysis.expense_parameters.cost_base_date" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.replacement_cost_override_reason')" :class="incomeFocusClass('expense_parameters.replacement_cost_override_reason')">超范围或人工取值说明input v-model="incomeAnalysis.expense_parameters.replacement_cost_override_reason" class="field-input" placeholder="采用值不取上限或超出范围时填写 /></label>
                        <label :id="incomeFocusId('expense_parameters.residual_rate')" :class="incomeFocusClass('expense_parameters.residual_rate')">残值率%<input v-model="incomeAnalysis.expense_parameters.residual_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.insurance_rate_permille')" :class="incomeFocusClass('expense_parameters.insurance_rate_permille')">保险费‰<input v-model="incomeAnalysis.expense_parameters.insurance_rate_permille" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.property_tax_rate')" :class="incomeFocusClass('expense_parameters.property_tax_rate')">房产税率%<input v-model="incomeAnalysis.expense_parameters.property_tax_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('expense_parameters.property_tax_reduction_rate')" :class="incomeFocusClass('expense_parameters.property_tax_reduction_rate')">房产税减免<input v-model="incomeAnalysis.expense_parameters.property_tax_reduction_rate" class="field-input compact-input" /></label>
                      </div>
                    </section>
                    <section class="cost-item-group income-cap-rate-highlight">
                      <header><div><strong>土地和房屋还原率</strong><small>正式归档前必须确认，Word 中生成表3-16。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="incomeFocusId('cap_rate_parameters.land_usage')" :class="incomeFocusClass('cap_rate_parameters.land_usage')">土地用途input v-model="incomeAnalysis.cap_rate_parameters.land_usage" class="field-input" /></label>
                        <label :id="incomeFocusId('cap_rate_parameters.income_land_cap_rate')" :class="incomeFocusClass('cap_rate_parameters.income_land_cap_rate')">土地还原率<input v-model="incomeAnalysis.cap_rate_parameters.income_land_cap_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('cap_rate_parameters.income_building_cap_rate')" :class="incomeFocusClass('cap_rate_parameters.income_building_cap_rate')">房屋还原率<input v-model="incomeAnalysis.cap_rate_parameters.income_building_cap_rate" class="field-input compact-input" /></label>
                        <label :id="incomeFocusId('cap_rate_parameters.use_term_years')" :class="incomeFocusClass('cap_rate_parameters.use_term_years')">土地使用年期<input v-model="incomeAnalysis.cap_rate_parameters.use_term_years" class="field-input compact-input" /></label>
                        <label class="income-confirm"><input type="checkbox" v-model="incomeAnalysis.cap_rate_parameters.confirmed" class="confirm-checkbox" /> 已确认还原率</label>
                      </div>
                    </section>
                    <div class="analysis-summary-strip">
                      <div :id="incomeFocusId('income_results.annual_gross_income')" :class="incomeFocusClass('income_results.annual_gross_income')">
                        <span>房地年总收益</span>
                        <strong :class="{ 'analysis-summary-value-pending': !incomeAnalysis.income_results?.annual_gross_income || incomeAnalysis.income_results?.annual_gross_income === '-' }">{{ incomeAnalysis.income_results?.annual_gross_income || '-' }}</strong>
                        <small>万元</small>
                      </div>
                      <div :id="incomeFocusId('income_results.total_expense')" :class="incomeFocusClass('income_results.total_expense')">
                        <span>房地年总费用</span>
                        <strong :class="{ 'analysis-summary-value-pending': !incomeAnalysis.income_results?.total_expense || incomeAnalysis.income_results?.total_expense === '-' }">{{ incomeAnalysis.income_results?.total_expense || '-' }}</strong>
                        <small>万元</small>
                      </div>
                      <div :id="incomeFocusId('income_results.land_net_income')" :class="incomeFocusClass('income_results.land_net_income')">
                        <span>土地年纯收益</span>
                        <strong :class="{ 'analysis-summary-value-pending': !incomeAnalysis.income_results?.land_net_income || incomeAnalysis.income_results?.land_net_income === '-' }">{{ incomeAnalysis.income_results?.land_net_income || '-' }}</strong>
                        <small>万元</small>
                      </div>
                      <div :id="incomeFocusId('income_results.total_land_price')" :class="incomeFocusClass('income_results.total_land_price')">
                        <span>待估宗地总地价</span>
                        <strong :class="{ 'analysis-summary-value-pending': !incomeAnalysis.income_results?.total_land_price || incomeAnalysis.income_results?.total_land_price === '-' }">{{ incomeAnalysis.income_results?.total_land_price || '-' }}</strong>
                        <small>万元</small>
                      </div>
                      <div :id="incomeFocusId('income_results.unit_land_price')" :class="incomeFocusClass('income_results.unit_land_price')">
                        <span>单位地价</span>
                        <strong :class="{ 'analysis-summary-value-pending': !incomeAnalysis.income_cap_price || incomeAnalysis.income_cap_price === '-' }">{{ incomeAnalysis.income_cap_price || '-' }}</strong>
                        <small>元/㎡</small>
                      </div>
                    </div>
                  </section>
                </template>

                <template v-if="activeProcessMethod.method_key === 'benchmark_corr'">
                  <div class="market-workspace-tabs">
                    <button v-for="item in benchmarkWorkspaceViews" :key="item.key"
                            :class="['icon-btn', { primary: benchmarkWorkspaceView === item.key }]"
                            @click="benchmarkWorkspaceView = item.key">
                      {{ item.label }}
                    </button>
                  </div>

                  <div class="analysis-summary-strip benchmark-result-strip">
                    <div v-if="benchmarkUsesRoutePrice" :id="benchmarkFocusId('parameters.route_price')" :class="benchmarkFocusClass('parameters.route_price')"><span>路线价 Po</span><strong>{{ benchmarkAnalysis.parameters?.route_price || '待匹配' }}</strong><small>元/㎡</small></div>
                    <div v-else :id="benchmarkFocusId('parameters.base_land_price')" :class="benchmarkFocusClass('parameters.base_land_price')"><span>级别基准地价</span><strong>{{ benchmarkAnalysis.parameters?.base_land_price || '待匹配' }}</strong><small>元/㎡</small></div>
                    <div v-if="benchmarkIsSplitRoutePrice" :id="benchmarkFocusId('parameters.base_land_price')" :class="benchmarkFocusClass('parameters.base_land_price')"><span>不临街级别价</span><strong>{{ benchmarkAnalysis.parameters?.base_land_price || '待匹配' }}</strong><small>元/㎡</small></div>
                    <div v-if="!benchmarkIsSingleRoutePrice" :id="benchmarkFocusId('parameters.sum_ki')" :class="benchmarkFocusClass('parameters.sum_ki')"><span>{{ benchmarkIsSplitRoutePrice ? '不临街 ∑Ki' : '∑Ki 区域因素' }}</span><strong>{{ benchmarkRegionalSum || benchmarkAnalysis.parameters?.sum_ki || '待计算' }}</strong><small>%</small></div>
                    <div v-else :id="benchmarkFocusId('parameters.ku')" :class="benchmarkFocusClass('parameters.ku')"><span>Ku 周边利用</span><strong>{{ benchmarkAnalysis.parameters?.ku || '待计算' }}</strong><small>—</small></div>
                    <div :id="benchmarkFocusId('parameters.kv')" :class="benchmarkFocusClass('parameters.kv')"><span>容积率 Kv</span><strong>{{ benchmarkAnalysis.parameters?.kv || '待计算' }}</strong><small>内插</small></div>
                    <div :id="benchmarkFocusId('parameters.ky')" :class="benchmarkFocusClass('parameters.ky')"><span>年期 Ky</span><strong>{{ benchmarkAnalysis.parameters?.ky || '待计算' }}</strong><small>—</small></div>
                    <div :id="benchmarkFocusId('result_values.benchmark_corr_price')" :class="benchmarkFocusClass('result_values.benchmark_corr_price')"><span>{{ benchmarkFormulaSymbol }}（最终单价）</span><strong>{{ benchmarkPriceDisplay || '待计算' }}</strong><small>元/㎡</small></div>
                  </div>
                  <div v-if="benchmarkAnalysis.support_status && benchmarkAnalysis.support_status !== 'supported'" class="method-warning-strip">
                    <strong>{{ benchmarkAnalysis.support_status === 'unsupported' ? '暂不可采用' : '待校核' }}</strong>
                    <span>{{ benchmarkSupportSummary }}</span>
                    <button v-if="benchmarkSupportActionTarget(activeProcessMethod)" class="warning-hotspot" @click="focusProcessSource(benchmarkSupportActionTarget(activeProcessMethod))">去校核</button>
                  </div>

                  <!-- 视图1：级别基准地价 -->
                  <section v-show="benchmarkWorkspaceView === 'base'" id="focus_item_benchmark_corr_analysis" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>确定级别基准地价（Po）</strong>
                      <span>按用途、级别自动匹配基准地价表（表3-2）；变更即时重算。</span>
                      <button class="icon-btn primary" @click="calculateBenchmarkCorrection">计算并校核</button>
                    </div>
                    <section class="cost-item-group">
                      <header><div><strong>用途与级别</strong><small>对应《城区级别基准地价表》。选择后自动取对应基准地价。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('coverage_scope')" :class="benchmarkFocusClass('coverage_scope')">覆盖范围
                          <select v-model="benchmarkAnalysis.coverage_scope" class="field-input" @change="onBenchmarkCoverageScopeChange">
                            <option value="城区">城区</option>
                            <option value="乡镇">乡镇</option>
                          </select>
                        </label>
                        <label v-if="benchmarkAnalysis.coverage_scope === '乡镇'" :id="benchmarkFocusId('township_grade')" :class="benchmarkFocusClass('township_grade')">乡镇等别
                          <select v-model="benchmarkAnalysis.township_grade" class="field-input" @change="onBenchmarkParameterInput">
                            <option v-for="opt in benchmarkTownshipGradeOptions" :key="opt" :value="opt">{{ opt }}</option>
                          </select>
                        </label>
                        <label :id="benchmarkFocusId('land_use_type')" :class="benchmarkFocusClass('land_use_type')">土地用途
                          <select v-model="benchmarkAnalysis.land_use_type" class="field-input" @change="onBenchmarkLandUseTypeChange">
                            <option v-for="opt in benchmarkLandUseTypeOptions" :key="opt" :value="opt">{{ opt }}</option>
                          </select>
                        </label>
                        <label :id="benchmarkFocusId('land_level')" :class="benchmarkFocusClass('land_level')">土地级别
                          <select v-model="benchmarkAnalysis.land_level" class="field-input" @change="onBenchmarkParameterInput">
                            <option v-for="opt in (benchmarkAnalysis.tables?.base_price_table?.levels || ['一级','二级','三级','四级','五级'])" :key="opt" :value="opt">{{ opt }}</option>
                          </select>
                        </label>
                        <label :id="benchmarkFocusId('parameters.base_land_price')" :class="benchmarkFocusClass('parameters.base_land_price')">级别基准地价（元/㎡）
                          <input v-model="benchmarkAnalysis.parameters.base_land_price" class="field-input compact-input" @input="onBenchmarkParameterInput" />
                        </label>
                        <template v-if="benchmarkIsCommercial">
                          <label :id="benchmarkFocusId('frontage_mode')" :class="benchmarkFocusClass('frontage_mode')">商服测算路径
                            <select v-model="benchmarkAnalysis.frontage_mode" class="field-input" @change="onBenchmarkFrontageModeChange">
                              <option value="non_street">不临街：级别基准地价</option>
                              <option value="street_route_price">临街：路线价</option>
                              <option value="route_price_plus_non_street">临街+不临街：路线价与级别价加权</option>
                            </select>
                          </label>
                          <template v-if="benchmarkUsesRoutePrice">
                            <label :id="benchmarkFocusId('route_segment_id')" :class="benchmarkFocusClass('route_segment_id')">路线价段
                              <select v-model="benchmarkAnalysis.route_segment_id" class="field-input" @change="onBenchmarkRouteSegmentChange">
                                <option value="">请选择路线价段</option>
                                <option v-for="seg in benchmarkRouteSegments" :key="seg.id" :value="seg.id">{{ benchmarkRouteSegmentLabel(seg) }}</option>
                              </select>
                            </label>
                            <label :id="benchmarkFocusId('parameters.route_price')" :class="benchmarkFocusClass('parameters.route_price')">路线价 Po（元/㎡）
                              <input v-model="benchmarkAnalysis.parameters.route_price" class="field-input compact-input" @input="onBenchmarkParameterInput" placeholder="路线段未匹配时可人工填写" />
                            </label>
                            <label :id="benchmarkFocusId('parameters.route_price_source_note')" :class="benchmarkFocusClass('parameters.route_price_source_note')">Po 来源说明
                              <input v-model="benchmarkAnalysis.parameters.route_price_source_note" class="field-input" @input="onBenchmarkParameterInput" placeholder="人工填写 Po 时必须说明来源" />
                            </label>
                          </template>
                        </template>
                        <label :id="benchmarkFocusId('parameters.base_price_source')" :class="benchmarkFocusClass('parameters.base_price_source')">依据
                          <input v-model="benchmarkAnalysis.parameters.base_price_source" class="field-input" placeholder="如：通政发〔2026〕1号" />
                        </label>
                        <label :id="benchmarkFocusId('map_image_ids')" :class="benchmarkFocusClass('map_image_ids')">土地级别图/基准地价图
                          <input v-model="benchmarkMapImageIdsText" class="field-input" placeholder="填写或粘贴已归档图件编号，后续可接入上传归档" @change="onBenchmarkMapIdsChange" />
                        </label>
                      </div>
                      <div class="benchmark-map-upload">
                        <input id="benchmark-map-image-upload" type="file" accept="image/*" class="hidden-file-input" multiple @change="handleBenchmarkMapUpload" />
                        <button type="button" class="icon-btn" @click="triggerBenchmarkMapUpload">上传待估宗地土地级别示意图</button>
                        <span class="muted-text">可上传土地级别图、基准地价图或截图，正式归档图件后可同步图件编号。</span>
                        <div v-if="(benchmarkAnalysis.map_images || []).length" class="benchmark-map-preview-grid">
                          <div v-for="(image, index) in benchmarkAnalysis.map_images" :key="image.id || image.name || index" class="image-thumb-wrapper">
                            <img :src="image.data" class="image-thumb" alt="土地级别示意图预览" />
                            <div class="image-thumb-overlay">
                              <button type="button" class="table-action danger" @click.stop="removeBenchmarkMapImage(index)">删除</button>
                            </div>
                            <small>{{ image.name }}</small>
                          </div>
                        </div>
                      </div>
                    </section>
                    <section v-if="benchmarkUsesRoutePrice && benchmarkRouteSegments.length" class="cost-item-group">
                      <header><div><strong>通道县城区商业服务业用地路线价表</strong><small>临街路线价模式下选择路线价段；无法匹配时可人工填写 Po 并说明来源。</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-derived-table">
                          <thead><tr><th>编号</th><th>道路名称</th><th>起点</th><th>终点</th><th>级别</th><th>道路类型</th><th>标准深度</th><th>路线价</th></tr></thead>
                          <tbody>
                            <tr v-for="seg in benchmarkRouteSegments" :key="seg.id" :class="{ 'benchmark-row-active': seg.id === benchmarkAnalysis.route_segment_id }">
                              <td>{{ seg.id }}</td><td>{{ seg.road_name }}</td><td>{{ seg.route_start }}</td><td>{{ seg.route_end }}</td>
                              <td>{{ seg.level }}</td><td>{{ seg.road_type }}</td><td>{{ seg.standard_depth }}</td><td>{{ seg.route_price }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section v-if="benchmarkAnalysis.coverage_scope !== '乡镇' && benchmarkAnalysis.tables?.base_price_table?.rows?.length" class="cost-item-group">
                      <header><div><strong>表3-2 级别基准地价（参考）</strong><small>单位：元/平方米</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-derived-table">
                          <thead><tr><th>用地类型</th><th v-for="lv in (benchmarkAnalysis.tables.base_price_table.levels || [])" :key="lv">{{ lv }}</th></tr></thead>
                          <tbody>
                            <tr v-for="row in benchmarkAnalysis.tables.base_price_table.rows" :key="benchmarkBaseRowUseType(row)"
                                :class="{ 'benchmark-row-active': benchmarkBaseRowUseType(row) === benchmarkAnalysis.land_use_type }">
                              <td>{{ benchmarkBaseRowUseType(row) }}</td>
                              <td v-for="(lv, ci) in (benchmarkAnalysis.tables.base_price_table.levels || [])" :key="lv">{{ benchmarkBaseRowValue(row, lv, ci) }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section v-if="benchmarkAnalysis.coverage_scope === '乡镇' && benchmarkAnalysis.tables?.benchmark_township_base_price_table?.rows?.length" class="cost-item-group">
                      <header><div><strong>表3-2 乡镇级别基准地价（参考）</strong><small>按乡镇等别、用途和级别匹配，乡镇场景下替代城区级别基准地价表。</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-derived-table">
                          <thead>
                            <tr>
                              <th v-for="col in benchmarkAnalysis.tables.benchmark_township_base_price_table.columns" :key="col">{{ col }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, ri) in benchmarkAnalysis.tables.benchmark_township_base_price_table.rows" :key="ri"
                                :class="{ 'benchmark-row-active': row['乡镇等别'] === benchmarkAnalysis.township_grade && row['用地类型'] === benchmarkAnalysis.land_use_type }">
                              <td v-for="col in benchmarkAnalysis.tables.benchmark_township_base_price_table.columns" :key="col">{{ row[col] }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                  </section>

                  <!-- 视图2：∑Ki 区域/个别因素优劣度 -->
                  <section v-show="benchmarkWorkspaceView === 'factors'" id="focus_item_benchmark_corr_analysis_regional" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>{{ benchmarkIsSingleRoutePrice ? '临街路线价路径不使用区域因素修正（∑Ki）' : (benchmarkIsSplitRoutePrice ? '不临街部分区域因素修正系数（∑Ki）' : '宗地区域因素修正系数（∑Ki）') }}</strong>
                      <span>{{ benchmarkIsSingleRoutePrice ? '临街路线价已包含道路区位差异，当前分支改由商服临街宗地特别因素修正。' : (benchmarkIsSplitRoutePrice ? '拆分模式下仅不临街商服部分使用区域因素修正；临街部分走路线价和临街宗地特别因素修正。' : '逐项选择优劣度，自动查表取系数（表3-6/3-7/3-8）；合计即 ∑Ki。') }}</span>
                      <button class="icon-btn primary" @click="calculateBenchmarkCorrection">计算并校核</button>
                    </div>
                    <div class="analysis-summary-strip">
                      <div><span>{{ benchmarkIsSplitRoutePrice ? '不临街 ∑Ki 合计' : '∑Ki 合计' }}</span><strong>{{ benchmarkIsSingleRoutePrice ? '不参与' : (benchmarkRegionalSum || benchmarkAnalysis.parameters?.sum_ki || '待计算') }}</strong><small v-if="!benchmarkIsSingleRoutePrice">%</small></div>
                      <div><span>因素项数</span><strong>{{ benchmarkIsSingleRoutePrice ? '不适用' : (benchmarkAnalysis.regional_factors || []).length }}</strong><small v-if="!benchmarkIsSingleRoutePrice">项</small></div>
                    </div>
                    <section v-if="benchmarkIsSingleRoutePrice" class="cost-item-group">
                      <header><div><strong>路线价分支说明</strong><small>该路径公式不含 ∑Ki。</small></div></header>
                      <div class="analysis-warnings process-warnings">
                        <div class="warning-card-premium info">
                          <span>当前选择“临街：路线价”测算路径，公式为 Po×Ky×Kv×Kt×Ks×Ka×Kc×Kk×Kd×Ku＋Kf，不再编制宗地区位因素修正系数表。请在“年期/容积率/期日/其他修正”中填写周边土地利用类型、临街宽度、街角状态等专属修正项。</span>
                          <button class="warning-hotspot" @click="benchmarkWorkspaceView = 'corrections'">前往专属修正</button>
                        </div>
                      </div>
                    </section>
                    <section v-if="benchmarkIsSplitRoutePrice" class="cost-item-group">
                      <header><div><strong>商服面积分配</strong><small>临街面积=路线价段标准深度×临街宽度；其他面积=商服总面积-临街面积。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('parameters.commercial_area_m2')" :class="benchmarkFocusClass('parameters.commercial_area_m2')">商服总面积（㎡）
                          <input :value="benchmarkAnalysis.parameters?.commercial_area_m2 || benchmarkAnalysis.commercial_area_m2 || form.land_area.value || '待填写'" class="field-input compact-input" readonly title="默认引用第二部分土地面积；商住混合用途拆分后再扩展独立商服面积入口" />
                        </label>
                        <label :id="benchmarkFocusId('parameters.frontage_standard_depth_m')" :class="benchmarkFocusClass('parameters.frontage_standard_depth_m')">标准深度（米）
                          <input :value="benchmarkAnalysis.parameters?.frontage_standard_depth_m || benchmarkAnalysis.frontage_standard_depth_m || benchmarkFrontageStandardDepthValue() || '选择路线价段后自动匹配'" class="field-input compact-input" readonly />
                        </label>
                        <label>临街宽度（米）
                          <input v-model="benchmarkAnalysis.frontage_width_m" class="field-input compact-input" @input="onBenchmarkFrontageWidthInput" />
                        </label>
                        <label :id="benchmarkFocusId('parameters.frontage_area_m2')" :class="benchmarkFocusClass('parameters.frontage_area_m2')">临街商服面积（㎡）
                          <input :value="benchmarkAnalysis.parameters?.frontage_area_m2 || benchmarkAnalysis.frontage_area_m2 || '待计算'" class="field-input compact-input" readonly />
                        </label>
                        <label :id="benchmarkFocusId('parameters.non_frontage_area_m2')" :class="benchmarkFocusClass('parameters.non_frontage_area_m2')">其他商服面积（㎡）
                          <input :value="benchmarkAnalysis.parameters?.non_frontage_area_m2 || benchmarkAnalysis.non_frontage_area_m2 || '待计算'" class="field-input compact-input" readonly />
                        </label>
                        <label>平均临街深度（米）
                          <input :value="benchmarkAnalysis.frontage_depth_m || benchmarkAnalysis.parameters?.frontage_average_depth_m || '填写临街宽度后自动计算'" class="field-input compact-input" readonly title="由商服总面积÷临街宽度自动计算，用于 Kd" />
                        </label>
                      </div>
                    </section>
                    <section v-if="!benchmarkIsSingleRoutePrice" class="cost-item-group">
                      <header><div><strong>{{ benchmarkIsSplitRoutePrice ? '表3-8 不临街部分宗地地价区域因素修正系数表' : '表3-8 宗地地价区位因素修正系数表' }}</strong><small>选择优劣度后自动取得修正系数（%）。</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>因素</th><th>因子</th><th>因素说明</th><th>优劣度</th><th>修正系数（%）</th></tr></thead>
                          <tbody>
                            <tr v-for="(factor, index) in benchmarkAnalysis.regional_factors || []" :key="factor.key || index"
                                :id="benchmarkFocusId('regional_factors.' + index + '.coefficient')"
                                :class="benchmarkFocusClass('regional_factors.' + index + '.coefficient')">
                              <td>{{ factor.factor }}</td>
                              <td>{{ factor.indicator }}</td>
                              <td><input v-model="factor.description" class="field-input" :placeholder="benchmarkFactorDescriptionPlaceholder(factor)" /></td>
                              <td>
                                <select v-model="factor.level" class="field-input compact-input" @change="onBenchmarkRegionalLevelChange(factor)">
                                  <option v-for="opt in (factor.options || [])" :key="opt.label" :value="opt.label">{{ opt.label }}</option>
                                </select>
                              </td>
                              <td><input v-model="factor.coefficient" class="field-input compact-input" @input="onBenchmarkParameterInput" /></td>
                            </tr>
                            <tr v-if="!(benchmarkAnalysis.regional_factors || []).length">
                              <td colspan="5" class="muted-text">点击“计算并校核”，由后端按级别载入区域因素修正系数表。</td>
                            </tr>
                          </tbody>
                          <tfoot>
                            <tr><td colspan="4">合计 ∑Ki</td><td>{{ benchmarkRegionalSum || benchmarkAnalysis.parameters?.sum_ki || '待计算' }}</td></tr>
                          </tfoot>
                        </table>
                      </div>
                    </section>
                  </section>

                  <!-- 视图3：年期/容积率/期日/其他修正 -->
                  <section v-show="benchmarkWorkspaceView === 'corrections'" id="focus_item_benchmark_corr_analysis_corrections" class="market-workspace-panel">
                    <div class="analysis-toolbar">
                      <strong>年期 / 容积率/ 期日 / 面积形状景观朝向 / 开发程度修正</strong>
                      <span>参数变更即时反馈（防抖）；交互期不重建正文，点击“计算并校核”后写入。</span>
                      <button class="icon-btn primary" @click="calculateBenchmarkCorrection">计算并校核</button>
                    </div>
                    <section class="cost-item-group">
                      <header><div><strong>容积率修正系数（Kv）</strong><small>采用内插法，见表3-3。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('parameters.plot_ratio')" :class="benchmarkFocusClass('parameters.plot_ratio')">设定容积率
                          <span class="benchmark-linked-control">
                            <input :value="benchmarkLinkedPlotRatio || '待填写'" class="field-input compact-input" readonly />
                            <button type="button" class="table-action compact-action" @click="jumpToBenchmarkLinkedField('set_plot_ratio')">修改</button>
                          </span>
                        </label>
                        <label :id="benchmarkFocusId('parameters.kv')" :class="benchmarkFocusClass('parameters.kv')">Kv（内插结果）<input v-model="benchmarkAnalysis.parameters.kv" class="field-input compact-input" readonly /></label>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>使用年期修正系数（Ky）</strong><small>Ky=[1-1/(1+r)^m]/[1-1/(1+r)^n]，见表3-4。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('parameters.cap_rate')" :class="benchmarkFocusClass('parameters.cap_rate')">土地还原率 r（%）<input v-model="benchmarkAnalysis.parameters.cap_rate" class="field-input compact-input" @input="onBenchmarkParameterInput" /></label>
                        <label :id="benchmarkFocusId('parameters.set_term_years')" :class="benchmarkFocusClass('parameters.set_term_years')">设定使用年期 m
                          <span class="benchmark-linked-control">
                            <input :value="benchmarkLinkedUseTerm || '待填写'" class="field-input compact-input" readonly />
                            <button type="button" class="table-action compact-action" @click="jumpToBenchmarkLinkedField('land_use_term')">修改</button>
                          </span>
                        </label>
                        <label :id="benchmarkFocusId('parameters.legal_term_years')" :class="benchmarkFocusClass('parameters.legal_term_years')">法定最高年期 n<input :value="benchmarkLegalTermDisplay || '待匹配'" class="field-input compact-input" readonly title="按当前土地用途自动匹配法定最高出让年期" /></label>
                        <label :id="benchmarkFocusId('parameters.ky')" :class="benchmarkFocusClass('parameters.ky')">Ky（结果）<input v-model="benchmarkAnalysis.parameters.ky" class="field-input compact-input" readonly /></label>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>估价期日修正系数（Kt）</strong><small>Kt=(1+月率)^月数，表3-5。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('parameters.base_date')" :class="benchmarkFocusClass('parameters.base_date')">基准地价基准日<input v-model="benchmarkAnalysis.parameters.base_date" class="field-input compact-input" @input="onBenchmarkParameterInput" /></label>
                        <label :id="benchmarkFocusId('parameters.valuation_date')" :class="benchmarkFocusClass('parameters.valuation_date')">估价期日
                          <span class="benchmark-linked-control">
                            <input :value="benchmarkLinkedValuationDate || '待填写'" class="field-input compact-input" readonly />
                            <button type="button" class="table-action compact-action" @click="jumpToBenchmarkLinkedField('valuation_date')">修改</button>
                          </span>
                        </label>
                        <label :id="benchmarkFocusId('parameters.months_elapsed')" :class="benchmarkFocusClass('parameters.months_elapsed')">间隔月数<input v-model="benchmarkAnalysis.parameters.months_elapsed" class="field-input compact-input" @input="onBenchmarkParameterInput" /></label>
                        <label :id="benchmarkFocusId('parameters.monthly_growth_rate')" :class="benchmarkFocusClass('parameters.monthly_growth_rate')">月上涨率（%）<input v-model="benchmarkAnalysis.parameters.monthly_growth_rate" class="field-input compact-input" @input="onBenchmarkParameterInput" /></label>
                        <label :id="benchmarkFocusId('parameters.kt')" :class="benchmarkFocusClass('parameters.kt')">Kt（结果）<input v-model="benchmarkAnalysis.parameters.kt" class="field-input compact-input" readonly /></label>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>面积/形状/景观/朝向修正（Ks/Ka/Ke/Kto）</strong><small>选择优劣度后查表（表3-9至表3-12）自动取得系数。</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table cost-edit-table">
                          <thead><tr><th>修正项</th><th>优劣度</th><th>修正系数</th></tr></thead>
                          <tbody>
                            <tr v-for="item in benchmarkIndividualFactorRows" :key="item.key"
                                :id="benchmarkFocusId('individual_factors.' + item.key + '.coefficient')"
                                :class="benchmarkFocusClass('individual_factors.' + item.key + '.coefficient')">
                              <td>{{ item.label }}</td>
                              <td>
                                <select v-if="(item.data.options || []).length" v-model="item.data.level" class="field-input compact-input" @change="onBenchmarkIndividualLevelChange(item.data)">
                                  <option v-for="opt in item.data.options" :key="opt.label" :value="opt.label">{{ opt.label }}</option>
                                </select>
                                <span v-else>—</span>
                              </td>
                              <td><input v-model="item.data.coefficient" class="field-input compact-input" @input="onBenchmarkParameterInput" /></td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </section>
                    <section v-if="benchmarkIsCommercial" class="cost-item-group">
                      <header><div><strong>商业服务业用地专属修正（Ku/Kd/Kk/Kc）</strong><small>不临街路径只使用 Ku；临街路线价路径使用 Ku、Kd、Kk、Kc。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('ku_grade')" :class="benchmarkFocusClass('ku_grade')">周边土地利用类型
                          <select v-model="benchmarkAnalysis.ku_grade" class="field-input" @change="onBenchmarkKuChange">
                            <option value="">请选择</option>
                            <option v-for="opt in benchmarkKuOptions" :key="opt.label" :value="opt.label">{{ opt.label }}{{ opt.description ? ' - ' + opt.description : '' }}</option>
                          </select>
                        </label>
                        <label :id="benchmarkFocusId('parameters.ku')" :class="benchmarkFocusClass('parameters.ku')">Ku<input v-model="benchmarkAnalysis.parameters.ku" class="field-input compact-input" readonly /></label>
                        <template v-if="benchmarkUsesRoutePrice">
                          <label :id="benchmarkFocusId('parameters.route_road_type')" :class="benchmarkFocusClass('parameters.route_road_type')">道路类型
                            <input v-if="benchmarkSelectedRouteSegment" :value="benchmarkRouteRoadTypeDisplay || '选择路线价段后自动匹配'" class="field-input compact-input" readonly />
                            <select v-else v-model="benchmarkAnalysis.parameters.route_road_type" class="field-input compact-input" @change="onBenchmarkParameterInput" title="未匹配路线价段、人工填写 Po 时才需手动选择">
                              <option value="">请选择</option>
                              <option value="主干道">主干道</option>
                              <option value="次干道">次干道</option>
                              <option value="支路">支路</option>
                            </select>
                          </label>
                          <label v-if="!benchmarkSelectedRouteSegment" :id="benchmarkFocusId('parameters.route_road_grade')" :class="benchmarkFocusClass('parameters.route_road_grade')">道路等级匹配来源
                            <select v-model="benchmarkAnalysis.parameters.route_road_grade" class="field-input compact-input" @change="onBenchmarkRoadGradeChange">
                              <option value="">请选择</option>
                              <option value="混合型主干道">混合型主干道</option>
                              <option value="生活型主干道">生活型主干道</option>
                              <option value="交通型主干道">交通型主干道</option>
                              <option value="生活型次干道">生活型次干道</option>
                              <option value="交通型次干道">交通型次干道</option>
                              <option value="支路">支路</option>
                            </select>
                          </label>
                          <label :id="benchmarkFocusId('frontage_relation')" :class="benchmarkFocusClass('frontage_relation')">临街关系
                            <select v-model="benchmarkAnalysis.frontage_relation" class="field-input compact-input" @change="onBenchmarkFrontageRelationChange">
                              <option value="adjacent">紧邻道路，按面积/宽度自动计算</option>
                              <option value="setback">与道路有退距，人工填写有效临街深度</option>
                            </select>
                          </label>
                          <label :id="benchmarkFocusId('frontage_depth_m')" :class="benchmarkFocusClass('frontage_depth_m')">临街深度（米）
                            <input v-if="benchmarkAnalysis.frontage_relation === 'setback'" v-model="benchmarkAnalysis.frontage_depth_m" class="field-input compact-input" @input="onBenchmarkFrontageDepthInput" placeholder="填写有效临街深度" />
                            <input v-else :value="benchmarkAnalysis.frontage_depth_m || '填写临街宽度后自动计算'" class="field-input compact-input" readonly title="由宗地面积÷临街宽度自动计算，不能单独修改" />
                          </label>
                          <label :id="benchmarkFocusId('parameters.kd')" :class="benchmarkFocusClass('parameters.kd')">Kd<input v-model="benchmarkAnalysis.parameters.kd" class="field-input compact-input" readonly /></label>
                          <label :id="benchmarkFocusId('frontage_width_m')" :class="benchmarkFocusClass('frontage_width_m')">临街宽度（米）<input v-model="benchmarkAnalysis.frontage_width_m" class="field-input compact-input" @input="onBenchmarkFrontageWidthInput" /></label>
                          <label :id="benchmarkFocusId('parameters.kk')" :class="benchmarkFocusClass('parameters.kk')">Kk<input v-model="benchmarkAnalysis.parameters.kk" class="field-input compact-input" readonly /></label>
                          <label :id="benchmarkFocusId('is_corner')" :class="benchmarkFocusClass('is_corner')">是否街角地
                            <select v-model="benchmarkAnalysis.is_corner" class="field-input compact-input" @change="onBenchmarkCornerChange">
                              <option :value="false">否</option>
                              <option :value="true">是</option>
                            </select>
                          </label>
                          <template v-if="benchmarkAnalysis.is_corner">
                            <label :id="benchmarkFocusId('corner_route_price_a')" :class="benchmarkFocusClass('corner_route_price_a')">相邻路线价一（元/㎡）<input v-model="benchmarkAnalysis.corner_route_price_a" class="field-input compact-input" @input="onBenchmarkCornerPriceInput" /></label>
                            <label :id="benchmarkFocusId('corner_route_price_b')" :class="benchmarkFocusClass('corner_route_price_b')">相邻路线价二（元/㎡）<input v-model="benchmarkAnalysis.corner_route_price_b" class="field-input compact-input" @input="onBenchmarkCornerPriceInput" /></label>
                            <label :id="benchmarkFocusId('parameters.corner_main_route_price')" :class="benchmarkFocusClass('parameters.corner_main_route_price')">正街路线价<input v-model="benchmarkAnalysis.parameters.corner_main_route_price" class="field-input compact-input" readonly /></label>
                            <label :id="benchmarkFocusId('parameters.corner_side_route_price')" :class="benchmarkFocusClass('parameters.corner_side_route_price')">旁街路线价<input v-model="benchmarkAnalysis.parameters.corner_side_route_price" class="field-input compact-input" readonly /></label>
                            <label :id="benchmarkFocusId('parameters.corner_price_ratio')" :class="benchmarkFocusClass('parameters.corner_price_ratio')">正街/旁街比例<input v-model="benchmarkAnalysis.parameters.corner_price_ratio" class="field-input compact-input" readonly /></label>
                          </template>
                          <label :id="benchmarkFocusId('parameters.kc')" :class="benchmarkFocusClass('parameters.kc')">Kc<input v-model="benchmarkAnalysis.parameters.kc" class="field-input compact-input" readonly /></label>
                        </template>
                      </div>
                    </section>
                    <section class="cost-item-group">
                      <header><div><strong>开发程度修正（Kf）</strong><small>基准内涵开发程度来自通道县技术报告；与第二部分设定开发程度一致时 Kf=0，不一致时需校核修正额。</small></div></header>
                      <div class="income-profile-grid">
                        <label :id="benchmarkFocusId('parameters.base_development')" :class="benchmarkFocusClass('parameters.base_development')">基准开发程度<input v-model="benchmarkAnalysis.parameters.base_development" class="field-input" readonly /></label>
                        <label :id="benchmarkFocusId('parameters.set_development')" :class="benchmarkFocusClass('parameters.set_development')">设定开发程度
                          <span class="benchmark-linked-control">
                            <input :value="benchmarkLinkedSetDevelopment || '待填写'" class="field-input" readonly />
                            <button type="button" class="table-action compact-action" @click="jumpToBenchmarkLinkedField('land_development_set')">修改</button>
                          </span>
                        </label>
                        <label :id="benchmarkFocusId('parameters.kf')" :class="benchmarkFocusClass('parameters.kf')">Kf（元/㎡）<input v-model="benchmarkAnalysis.parameters.kf" class="field-input compact-input" @input="onBenchmarkParameterInput" /></label>
                      </div>
                    </section>
                    <section class="cost-item-group benchmark-formula-group">
                      <header><div><strong>{{ benchmarkFormulaSymbol }} 计算（设定开发程度条件下宗地地价）</strong><small>{{ benchmarkFormulaPreview }}</small></div></header>
                      <p class="benchmark-formula-line">
                        {{ benchmarkFormulaValuePreview }}
                        <strong>={{ benchmarkPriceDisplay || '待计算' }} 元/㎡</strong>
                      </p>
                    </section>
                  </section>
                </template>

                <div v-show="activeProcessMethod.method_key === 'market_comp'
                  ? marketWorkspaceView === 'narratives'
                  : activeProcessMethod.method_key === 'cost_approx'
                    ? costWorkspaceView === 'narratives'
                    : activeProcessMethod.method_key === 'income_cap'
                      ? incomeWorkspaceView === 'narratives'
                    : activeProcessMethod.method_key === 'benchmark_corr'
                      ? benchmarkWorkspaceView === 'narratives'
                    : true">
                  <div class="process-content-layout">
                    <aside class="process-local-nav" aria-label="第五部分正文导航">
                      <button v-for="block in processRenderableContentBlocks(activeProcessMethod)" :key="`nav_${block.type}_${block.key}`"
                              type="button" class="process-local-nav-item"
                              @click="scrollToProcessBlock(block)">
                        {{ processBlockNavLabel(activeProcessMethod, block) }}
                      </button>
                    </aside>
                    <div class="process-content-main">
                  <template v-for="block in processRenderableContentBlocks(activeProcessMethod)" :key="`${block.type}_${block.key}`">
                    <article v-if="block.type === 'narrative' && processNarrative(activeProcessMethod, block.key)"
                             :id="processBlockAnchorId(block)"
                             :class="['process-section', { 'needs-adjustment': processNarrative(activeProcessMethod, block.key).review_state === 'needs_adjustment' }]">
                      <header>
                        <div>
                          <strong>{{ processNarrative(activeProcessMethod, block.key).title }}</strong>
                          <small>{{ processNarrative(activeProcessMethod, block.key).override_text !== null ? '人工覆盖生效中' : '系统草稿' }}</small>
                        </div>
                        <button v-if="processNarrative(activeProcessMethod, block.key).editable && processNarrative(activeProcessMethod, block.key).override_text !== null"
                                class="table-action" @click="restoreProcessNarrative(processNarrative(activeProcessMethod, block.key))">恢复系统草稿</button>
                      </header>
                      <p v-if="processNarrative(activeProcessMethod, block.key).review_message" class="process-review-message">
                        {{ processNarrative(activeProcessMethod, block.key).review_message }}
                      </p>
                      <textarea v-if="processViewMode === 'edit' && processNarrative(activeProcessMethod, block.key).editable"
                                v-model="processNarrative(activeProcessMethod, block.key).effective_text"
                                class="field-input process-narrative-editor"
                                @change="saveProcessNarrativeOverride(processNarrative(activeProcessMethod, block.key))"></textarea>
                      <div v-else-if="processViewMode === 'hotspot' && processNarrativeSegments(processNarrative(activeProcessMethod, block.key)).length"
                           class="process-narrative-preview perspective-rich-viewer">
                        <template v-for="(seg, segIndex) in processNarrativeSegments(processNarrative(activeProcessMethod, block.key))" :key="`${block.key}_seg_${segIndex}`">
                          <span v-if="seg.field || seg.fields" :class="getDocRefClass(seg)" @click="handleProcessSegmentClick(seg)" @mouseenter="showRefTooltip(seg, $event)" @mouseleave="hideRefTooltip">{{ seg.text }}</span>
                          <span v-else>{{ seg.text }}</span>
                        </template>
                      </div>
                      <div v-else class="process-narrative-preview">{{ processNarrative(activeProcessMethod, block.key).effective_text || '【本段尚未生成】' }}</div>
                      <!-- <div v-if="processViewMode === 'hotspot'" class="process-hotspots">
                        <button v-for="refKey in processNarrative(activeProcessMethod, block.key).hotspot_refs" :key="refKey" class="table-action" @click="focusProcessSource(refKey)">{{ refKey }}</button>
                      </div> -->
                    </article>

                    <article v-else-if="block.type === 'table' && processTable(activeProcessMethod, block.key)"
                             :id="processBlockAnchorId(block)"
                             class="process-section process-table-section">
                      <header>
                        <div><strong>{{ processTable(activeProcessMethod, block.key).report_title || processTable(activeProcessMethod, block.key).title }}</strong><small>只读结构化派生内容，与正式报告同步</small></div>
                        <button v-if="processTable(activeProcessMethod, block.key).source_target" class="table-action" @click="openProcessSource(processTable(activeProcessMethod, block.key).source_target)">
                          {{ processTableActionLabel(processTable(activeProcessMethod, block.key)) }}
                        </button>
                      </header>
                      <div class="table-scroll">
                        <table class="comparable-table process-report-table">
                          <thead>
                            <tr v-for="(headerRow, headerIndex) in processTableHeaderRows(processTable(activeProcessMethod, block.key))" :key="`${block.key}_header_${headerIndex}`">
                              <th v-for="(cell, cellIndex) in headerRow" v-show="!cell.hidden" :key="`${block.key}_header_${headerIndex}_${cellIndex}`"
                                  :colspan="cell.colspan || 1" :rowspan="cell.rowspan || 1">{{ processTableHeaderCellLabel(cell) }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, rowIndex) in processTableDisplayRows(processTable(activeProcessMethod, block.key))" :key="`${block.key}_${rowIndex}`">
                              <td v-for="(cell, columnIndex) in row" v-show="!cell.hidden" :key="columnIndex" :rowspan="cell.rowspan || 1"
                                  :colspan="cell.colspan || 1"
                                  :class="{ 'process-ref-cell': cell.ref, 'computed-ref-cell': isComputedHotspotField(cell.ref) }"
                                  :title="cell.ref ? '点击定位来源字段' : ''"
                                  @click="cell.ref && focusProcessSource(cell.ref)">{{ cell.value || '待校核' }}</td>
                            </tr>
                            <tr v-if="!processTable(activeProcessMethod, block.key).rows?.length"><td :colspan="processTable(activeProcessMethod, block.key).columns.length">尚无结构化数据。</td></tr>
                          </tbody>
                        </table>
                      </div>
                    </article>

                    <article v-else-if="block.type === 'result' && processResult(activeProcessMethod, block.key)" :id="processBlockAnchorId(block)" class="process-section process-table-section">
                      <header><div><strong>{{ processResult(activeProcessMethod, block.key).label }}</strong><small>计算结果只读，与正式报告同步</small></div></header>
                      <div class="table-scroll">
                        <table class="comparable-table process-report-table process-result-table">
                          <thead><tr><th>项目</th><th>结果</th><th>单位</th><th>公式</th></tr></thead>
                          <tbody>
                            <tr>
                              <td>{{ processResult(activeProcessMethod, block.key).label }}</td>
                              <td>{{ processResult(activeProcessMethod, block.key).value || '待计算' }}</td>
                              <td>{{ processResult(activeProcessMethod, block.key).unit }}</td>
                              <td>{{ processResult(activeProcessMethod, block.key).formula }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </article>
                  </template>
                    </div>
                  </div>
                </div>

                <div v-if="activeFactorGuide" class="comparable-drawer-backdrop" @click.self="closeFactorGuide">
                  <aside class="comparable-drawer factor-guide-drawer">
                    <div class="comparable-drawer-header">
                      <div><strong>{{ activeFactorGuide.factor.label }}</strong><small>{{ activeFactorGuide.factor.group }} 路 一次校核估价对象及实例 A/B/C</small></div>
                      <button class="table-action" @click="closeFactorGuide">关闭</button>
                    </div>
                    <div class="factor-guide-rule">
                      <span>{{ factorConfirmedCount(activeFactorGuide.factor) === comparableSlots.length ? '本报告因素已校核' : (activeFactorGuide.factor.review_status === 'confirmed' ? '规则模板已校核' : '规则模板待校核') }}</span>
                      <p>{{ activeFactorGuide.factor.help_text || '请结合实例资料和现场调查判断条件及指数。' }}</p>
                    </div>
                    <section class="factor-guide-subject">
                      <h3>估价对象条件</h3>
                      <div class="factor-guide-subject-fields">
                        <label class="subject-val-label"
                               :id="marketFocusId('factors.' + activeFactorGuide.factor.key + '.subject_value')"
                               :class="marketFocusClass('factors.' + activeFactorGuide.factor.key + '.subject_value')">
                          <span>条件值</span>
                          <input v-model="activeFactorGuide.factor.subject_value" class="field-input" @input="markFactorGuideDirty" />
                        </label>
                        <div v-if="activeFactorGuide.factor.key === 'transaction_time' && marketNeedsTimeAdjustment" class="special-parameter-box time-param">
                          <label :id="marketFocusId('monthly_growth_rate')" :class="marketFocusClass('monthly_growth_rate')">
                            <span>月平均增长率（%）</span>
                            <input v-model="marketMonthlyGrowthRate" class="field-input highlight-parameter" @input="markMarketCalculationParameter('monthly_growth_rate', marketMonthlyGrowthRate)" />
                          </label>
                          <small class="param-tip">※ 交易期日修正用参数</small>
                        </div>
                        <div v-if="activeFactorGuide.factor.key === 'use_term' && marketNeedsTermAdjustment" class="special-parameter-box term-param">
                          <label :id="marketFocusId('land_reduction_rate')" :class="marketFocusClass('land_reduction_rate')">
                            <span>年期修正用土地还原率（%）</span>
                            <input v-model="marketLandReductionRate" class="field-input highlight-parameter" @input="markMarketCalculationParameter('land_reduction_rate', marketLandReductionRate)" />
                          </label>
                          <small class="param-tip">※ 使用年期修正用参数</small>
                        </div>
                      </div>
                    </section>
                    <div class="factor-guide-case-grid">
                      <section v-for="slot in comparableSlots" :key="`guide_${slot}`"
                               :id="marketFocusId('factors.' + activeFactorGuide.factor.key + '.cases.' + slot)"
                               :class="['factor-guide-case', marketFocusClass('factors.' + activeFactorGuide.factor.key + '.cases.' + slot)]">
                        <header>
                          <div><strong>实例 {{ slot }}</strong><small>{{ selectedComparableCase(slot)?.project_name || '未选择实例' }}</small></div>
                          <span :class="['factor-case-state', { complete: activeFactorGuide.factor.cases?.[slot]?.confirmed }]">{{ activeFactorGuide.factor.cases?.[slot]?.confirmed ? '已确认' : '待确认' }}</span>
                        </header>
                        <div v-if="activeFactorGuide.factor.levels?.length" class="factor-level-options">
                          <button v-for="level in activeFactorGuide.factor.levels" :key="`${slot}_${level.label}_${level.index}`"
                                  :class="{ selected: activeFactorGuide.factor.cases?.[slot]?.level_label === level.label }"
                                  @click="applyFactorLevel(level, slot)">
                            <strong>{{ level.label }}</strong><span>指数 {{ level.index }}</span><small>{{ level.description }}</small>
                          </button>
                        </div>
                        <div class="factor-guide-fields">
                          <label :id="marketFocusId('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.value')" :class="marketFocusClass('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.value')">条件值input v-model="activeFactorGuide.factor.cases[slot].value" class="field-input" @input="markActiveFactorOverride(slot)" /></label>
                          <label :id="marketFocusId('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.index')" :class="marketFocusClass('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.index')">指数<input v-model="activeFactorGuide.factor.cases[slot].index" class="field-input" @input="markActiveFactorOverride(slot)" /></label>
                          <label>来源<input :value="factorSourceLabel(activeFactorGuide.factor.cases[slot].source || activeFactorGuide.factor.source)" class="field-input" readonly /></label>
                          <label class="factor-guide-reason" :id="marketFocusId('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.override_reason')" :class="marketFocusClass('factors.' + activeFactorGuide.factor.key + '.cases.' + slot + '.override_reason')">覆盖说明<input v-model="activeFactorGuide.factor.cases[slot].override_reason" class="field-input" placeholder="人工覆盖建议时填写依据" @input="markActiveFactorOverride(slot)" /></label>
                        </div>
                      </section>
                    </div>
                    <div class="comparable-drawer-actions">
                      <span>{{ factorGuideDirty ? '有尚未确认的修改' : '修改后需重新确认并计算' }}</span>
                      <button class="icon-btn primary" @click="confirmActiveFactor" :disabled="!activeFactorCanConfirm">确认该因素A/B/C</button>
                    </div>
                  </aside>
                </div>
              </section>
            </template>
          </div>

          <div v-show="activeTab === 'p6'" class="tab-pane comparable-workspace">
            <div class="section-title-bar">
              <span class="card-title">比较实例库</span>
              <div class="comparable-header-actions">
                <span class="comparable-status" :class="{ complete: selectedComparableCount === 3 }">A/B/C 已选{{ selectedComparableCount }} / 3</span>
                <button class="icon-btn primary" @click="openCurrentMarketAnalysis('instances')">前往当前报告分析</button>
              </div>
            </div>

            <div class="comparable-view-tabs">
              <button v-for="item in comparableViews" :key="item.key"
                      :class="['icon-btn', { primary: comparableView === item.key }]"
                      @click="comparableView = item.key; onComparableViewChange(item.key)">
                {{ item.label }}
              </button>
            </div>

            <section v-show="comparableView === 'crawl'" class="comparable-panel">
              <div v-if="landChinaAccessStatus?.blocked" class="analysis-warnings">
                <strong>土地市场网访问冷却中</strong>
                <p>{{ landChinaAccessText(landChinaAccessStatus) }}</p>
              </div>
              <p v-if="landChinaAccessStatus" class="access-channel-line">
                访问通道：{{ landChinaAccessChannelText(landChinaAccessStatus) }}
              </p>
              <p v-if="landChinaAccessStatus && !landChinaAccessStatus.proxy_enabled" class="access-channel-hint">
                当前为本机直连；若土地市场网页面或抓取仍显示 Network Error，通常是官网 WAF 拦截了本机出口，请启用云服务器爬取。
              </p>
              <div class="cloud-proxy-settings">
                <label class="checkbox-field">
                  <input v-model="cloudProxyForm.enabled" type="checkbox" @change="toggleCloudProxyEnabled" />
                  启用云服务器爬取
                </label>
                <input v-model="cloudProxyForm.proxy_url" class="field-input" placeholder="http://服务器IP:8787/landchina" />
                <input v-model="cloudProxyForm.proxy_token" type="password" class="field-input" :placeholder="cloudProxyConfig?.token_set ? 'Token 已设置，留空表示不修改' : '填写云服务器 Token'" />
                <span class="cloud-proxy-token-state">{{ cloudProxyConfig?.token_set ? 'Token 已设置' : 'Token 未设置' }}</span>
                <button class="icon-btn primary" @click="saveCloudProxyConfig">保存配置</button>
                <button class="icon-btn" @click="testCloudProxyConfig">测试连接</button>
                <button class="icon-btn danger" @click="clearCloudProxyToken" :disabled="!cloudProxyConfig?.token_set">清除密钥</button>
              </div>
              <div class="comparable-filter-grid">
                <label>行政区代码<input v-model="crawlFilters.xzq_dm" class="field-input" placeholder="通道县 431230；道县 431124" /></label>
                <label>开始日期input v-model="crawlFilters.start_date" type="date" class="field-input" /></label>
                <label>结束日期<input v-model="crawlFilters.end_date" type="date" class="field-input" /></label>
                <label>土地用途
                  <select v-model="crawlFilters.land_usage_key" class="field-input">
                    <option value="">全部用途</option>
                    <option v-for="item in landUsageOptions" :key="`crawl_${item.key}`" :value="item.key">{{ item.label }}</option>
                  </select>
                </label>
                <label>供应方式<input v-model="crawlFilters.supply_method" class="field-input" placeholder="如：挂牌出让" /></label>
                <label>坐落关键词（可选）<input v-model="crawlFilters.location" class="field-input" placeholder="如：双江镇；不要填县名" /></label>
                <label>电子监管号<input v-model="crawlFilters.electronic_supervision_no" class="field-input" /></label>
                <label class="checkbox-field"><input v-model="crawlFilters.refresh_complete_details" type="checkbox" /> 强制刷新完整详情</label>
              </div>
              <div class="comparable-actions">
                <button class="icon-btn primary" @click="startComparableCrawl" :disabled="crawlJob?.status === 'running' || landChinaAccessStatus?.blocked">开始抓取</button>
                <button class="icon-btn danger" @click="cancelComparableCrawl" :disabled="!crawlJob || !['queued','running'].includes(crawlJob.status)">取消任务</button>
                <button class="icon-btn" @click="checkLandChinaAccessStatus">检查访问状态</button>
              </div>
              <div v-if="crawlJob" class="crawl-progress">
                <div>
                  <strong>{{ crawlPhaseLabel(crawlJob) }}</strong>
                  <span>已入库 {{ crawlJob.saved || 0 }} / {{ crawlJob.total || 0 }}，详情完整 {{ crawlJob.complete || 0 }}，待补全 {{ crawlJob.partial || 0 }}</span>
                </div>
                <progress :value="crawlJob.processed || crawlJob.saved || 0" :max="Math.max(crawlJob.total || 1, 1)"></progress>
                <p v-if="crawlJob.range_count">列表切片 {{ crawlJob.range_processed || 0 }} / {{ crawlJob.range_count }}，已发现 {{ crawlJob.listed || crawlJob.total || 0 }} 宗。</p>
                <p v-if="crawlJob.rate_limited">官网限流 {{ crawlJob.rate_limited }} 次，系统已自动降速并冷却。</p>
                <p v-if="crawlJob.stopped_reason">{{ crawlJob.stopped_reason }}</p>
                <p v-if="crawlJob.errors?.length">{{ crawlJob.errors[crawlJob.errors.length - 1] }}</p>
              </div>
            </section>

            <section id="comparable-library-panel" v-show="comparableView === 'library'" class="comparable-panel">
              <div class="comparable-filter-grid">
                <label>用途分类
                  <select v-model="libraryFilters.land_usage_key" class="field-input">
                    <option value="">全部用途</option>
                    <option v-for="item in landUsageOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
                  </select>
                </label>
                <label>开始日期<input v-model="libraryFilters.start_date" type="date" class="field-input" /></label>
                <label>结束日期<input v-model="libraryFilters.end_date" type="date" class="field-input" /></label>
                <label>供应方式<input v-model="libraryFilters.supply_method" class="field-input" /></label>
                <label>行政区
                  <select v-model="libraryFilters.xzq_dm" class="field-input">
                    <option value="">全部行政区</option>
                    <option v-for="item in comparableRegionOptions" :key="item.code" :value="item.code">
                      {{ comparableRegionOptionLabel(item) }}
                    </option>
                  </select>
                </label>
                <label>电子监管号<input v-model="libraryFilters.electronic_supervision_no" class="field-input" /></label>
                <label>关键词<input v-model="libraryFilters.keyword" class="field-input" /></label>
              </div>
              <div class="comparable-actions">
                <button class="icon-btn primary" @click="loadComparableCases">查询实例库</button>
                <button class="icon-btn" @click="exportComparableCases">导出当前筛选</button>
                <span>共 {{ comparableTotal }} 宗</span>
              </div>

              <div class="table-scroll">
                <table class="comparable-table">
                  <colgroup>
                    <col style="width: 140px;" /> <!-- 电子监管号-->
                    <col style="width: 220px;" /> <!-- 项目名称/坐落 -->
                    <col style="width: 100px;" /> <!-- 用途-->
                    <col style="width: 80px;" />  <!-- 供地方式 -->
                    <col style="width: 120px;" /> <!-- 土地使用权人 -->
                    <col style="width: 90px;" />  <!-- 合同签订日期 -->
                    <col style="width: 80px;" />  <!-- 面积㎡-->
                    <col style="width: 70px;" />  <!-- 使用年限 -->
                    <col style="width: 70px;" />  <!-- 土地级别 -->
                    <col style="width: 90px;" />  <!-- 成交价格万元 -->
                    <col style="width: 100px;" /> <!-- 地面单价元/㎡-->
                    <col style="width: 130px;" /> <!-- A/B/C -->
                    <col style="width: 70px;" />  <!-- 官网 -->
                    <col style="width: 100px;" /> <!-- 补充 -->
                  </colgroup>
                  <thead>
                    <tr>
                      <th class="sticky-left-1">电子监管号</th>
                      <th class="sticky-left-2">项目名称/坐落</th>
                      <th>用途</th>
                      <th>供地方式</th>
                      <th>土地使用权人</th>
                      <th>合同签订日期</th>
                      <th>面积㎡</th>
                      <th>使用年限</th>
                      <th>土地级别</th>
                      <th>成交价格万元</th>
                      <th>地面单价元/㎡</th>
                      <th class="sticky-right-abc">A/B/C</th>
                      <th class="sticky-right-web">官网</th>
                      <th class="sticky-right-opt">补充</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in comparableCases" :key="item.id"
                        :class="{
                          'row-selected-a': selectedComparableIds['A'] === item.id,
                          'row-selected-b': selectedComparableIds['B'] === item.id,
                          'row-selected-c': selectedComparableIds['C'] === item.id
                        }">
                      <td class="sticky-left-1">{{ item.electronic_supervision_no || item.gd_guid }}</td>
                      <td class="sticky-left-2"><strong>{{ item.project_name || '未命名项目' }}</strong><small>{{ item.location }}</small></td>
                      <td>{{ item.land_usage_raw }}<small>{{ item.land_usage_first_level || item.land_usage_key }}</small></td>
                      <td>{{ item.supply_method || '-' }}</td>
                      <td>{{ item.recipient || '-' }}</td>
                      <td>{{ item.transaction_date }}</td>
                      <td>{{ item.area_sqm }}</td>
                      <td>{{ item.use_term_years ? `${item.use_term_years}年` : '—' }}</td>
                      <td>{{ item.land_level || '-' }}</td>
                      <td>{{ item.total_price_wan || '-' }}</td>
                      <td class="unit-price-cell">{{ item.unit_price_sqm }}</td>
                      <td class="slot-actions sticky-right-abc">
                        <button v-for="slot in comparableSlots" :key="slot"
                                :class="{ selected: selectedComparableIds[slot] === item.id }"
                                :disabled="!item.unit_price_sqm"
                                :title="item.unit_price_sqm ? `设为实例 ${slot}` : '详情待补全，暂不能作为比较实例'"
                                @click="assignComparable(slot, item)">{{ slot }}</button>
                      </td>
                      <td class="sticky-right-web">
                        <button class="table-action" @click="openLandChinaSupplyDetail(item)" :disabled="!landChinaSupplyDetailUrl(item)">详情页</button>
                      </td>
                      <td class="sticky-right-opt">
                        <button class="table-action" @click="editComparableCase(item)">编辑</button>
                        <small>{{ item.detail_status === 'complete' ? '详情完整' : '待补全' }}</small>
                      </td>
                    </tr>
                    <tr v-if="!comparableCases.length"><td colspan="14">实例库暂无匹配记录，请先抓取或调整筛选条件。</td></tr>
                  </tbody>
                </table>
              </div>

              <div v-if="editingComparableCase" class="comparable-drawer-backdrop" @click.self="closeComparableCaseEditor">
                <aside class="comparable-drawer">
                  <div class="comparable-drawer-header">
                    <div>
                      <strong>{{ editingComparableCase.project_name || '未命名实例' }}</strong>
                      <small>{{ editingComparableCase.electronic_supervision_no || editingComparableCase.id }}</small>
                    </div>
                    <button class="table-action" @click="openLandChinaSupplyDetail(editingComparableCase)" :disabled="!landChinaSupplyDetailUrl(editingComparableCase)">官网详情</button>
                    <button class="table-action" @click="closeComparableCaseEditor">关闭</button>
                  </div>
                  <div class="case-status-strip">
                    <span>{{ editingComparableCase.land_usage_first_level || '用途待核实' }}</span>
                    <span>{{ editingComparableCase.detail_status === 'complete' ? '官网详情完整' : '官网详情待补全' }}</span>
                    <span :class="{ pending: Object.keys(editingComparableCase.manual_draft_fields || {}).length || caseChangedKeys.length }">
                      {{ caseDraftState || (Object.keys(editingComparableCase.manual_draft_fields || {}).length ? '有未确认草稿' : '无待确认草稿') }}
                    </span>
                  </div>

                  <section class="case-drawer-section">
                    <h3>官网基础信息</h3>
                    <div class="case-summary-grid">
                      <div v-for="[key, label] in comparableOfficialSummaryFields" :key="key">
                        <span>{{ label }}</span>
                        <strong>{{ editingComparableCase[key] || '-' }}</strong>
                      </div>
                    </div>
                  </section>

                  <section class="case-drawer-section">
                    <h3>市场比较法补充与区域因素</h3>
                    <div class="case-field-grid">
                      <label v-for="field in caseGuidedFields" :key="field.key">
                        <span>{{ field.label }} <em :class="`source-${caseFieldStatus(field.key)}`">{{ caseFieldStatusLabel(field.key) }}</em></span>
                        <input v-model="caseManualForm[field.key]" class="field-input" :placeholder="field.help" @input="markComparableDraftChanged(field.key)" />
                        <small>{{ field.help }}</small>
                      </label>
                    </div>
                  </section>

                  <details class="case-drawer-section advanced-section">
                    <summary>高级自定义字段</summary>
                    <textarea v-model="caseAdvancedJson" class="field-input code-editor" rows="7" @input="scheduleComparableAdvancedDraftSave"></textarea>
                  </details>

                  <div class="comparable-drawer-actions">
                    <span>{{ caseDraftState }}</span>
                    <button class="icon-btn" @click="saveComparableManualDraft()">保存草稿</button>
                    <button class="icon-btn primary" @click="confirmComparableManualFields">确认采用草稿</button>
                  </div>
                </aside>
              </div>
            </section>

            <section v-show="comparableView === 'schemes'" class="comparable-panel">
              <div class="scheme-impact-banner">
                <strong>全局规则管理</strong>
                <span>这里的修改影响未来新建报告，不会修改已经冻结规则快照的报告。保存前系统会展示变更摘要。</span>
              </div>
              <div class="scheme-toolbar">
                <select v-model="schemeUsageKey" class="field-input" @change="loadFactorScheme">
                  <option v-for="item in landUsageOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
                </select>
                <button class="icon-btn" @click="loadFactorScheme">重新载入</button>
                <button class="icon-btn" @click="addSchemeFactor">新增因子</button>
                <button class="icon-btn primary" @click="requestSaveFactorScheme">保存规则</button>
              </div>
              <div v-if="factorScheme" class="scheme-editor">
                <label class="scheme-name-field">方案名称<input v-model="factorScheme.name" class="field-input" /></label>
                <section v-for="(factors, group) in schemeFactorGroups" :key="group" class="scheme-group">
                  <h3>{{ group }} <span>{{ factors.length }} 项</span></h3>
                  <article v-for="factor in factors" :key="factor.key" :class="['scheme-factor-card', factor.review_status === 'confirmed' ? 'factor-state-confirmed' : 'factor-state-pending']">
                    <div class="scheme-factor-heading">
                      <input v-model="factor.label" class="field-input" />
                      <select v-model="factor.source" class="field-input">
                        <option value="official">官网</option>
                        <option value="calculated">系统计算</option>
                        <option value="manual">人工判断</option>
                      </select>
                      <select v-model="factor.review_status" class="field-input">
                        <option value="needs_review">待校核</option>
                        <option value="confirmed">已校核</option>
                      </select>
                      <label class="checkbox-field"><input v-model="factor.required" type="checkbox" /> 必填</label>
                      <label class="checkbox-field"><input v-model="factor.enabled" type="checkbox" /> 启用</label>
                      <button class="table-action" @click="removeSchemeFactor(factor.key)">删除</button>
                    </div>
                    <input v-model="factor.help_text" class="field-input" placeholder="判定说明：估价师应依据什么资料选择等级" />
                    <div class="factor-level-table">
                      <div v-for="(level, levelIndex) in factor.levels" :key="`${factor.key}_${levelIndex}`">
                        <input v-model="level.label" class="field-input" placeholder="等级" />
                        <input v-model="level.index" class="field-input compact-input" placeholder="指数" />
                        <input v-model="level.description" class="field-input" placeholder="判定口径" />
                        <button class="table-action" @click="removeSchemeLevel(factor, levelIndex)">删除</button>
                      </div>
                      <button class="table-action" @click="addSchemeLevel(factor)">添加等级</button>
                    </div>
                  </article>
                </section>
              </div>
              <details class="advanced-section" :open="showSchemeAdvanced" @toggle="showSchemeAdvanced = $event.target.open">
                <summary>高级 JSON 导入/导出</summary>
                <textarea v-model="factorSchemeJson" class="field-input code-editor" rows="18"></textarea>
                <button class="icon-btn" @click="applyFactorSchemeJson">将 JSON 应用到可视化方案</button>
              </details>
            </section>

            <div v-if="showSchemeChangeDialog" class="scheme-change-dialog-backdrop" @click.self="showSchemeChangeDialog = false">
              <section class="scheme-change-dialog">
                <header>
                  <div><strong>确认保存全局规则</strong><small>以下变更仅影响未来新建报告</small></div>
                  <button class="table-action" @click="showSchemeChangeDialog = false">关闭</button>
                </header>
                <ul class="scheme-change-list">
                  <li v-for="item in schemeChangeSummary" :key="item">{{ item }}</li>
                </ul>
                <div class="scheme-change-actions">
                  <button class="icon-btn" @click="showSchemeChangeDialog = false">取消</button>
                  <button class="icon-btn primary" @click="saveFactorScheme">确认保存规则</button>
                </div>
              </section>
            </div>
          </div>
        </div>
      </section>

      <div class="base-price-drawer" :class="{ 'drawer-open': showBasePriceDrawer }">
        <div class="drawer-header">
          <h2>🗺️ 基准地价资料</h2>
          <div class="drawer-actions">
            <button class="icon-btn" @click="showOCR = true; ocrType = 'base_price_report'">上传识别</button>
            <button class="icon-btn danger" @click="showBasePriceDrawer = false">✖ 关闭</button>
          </div>
        </div>
        <div class="base-price-drawer-body">
          <div class="base-price-summary">
            <div>
              <div class="base-price-summary-title">跨章节资料源</div>
              <div class="base-price-summary-copy">这里填写的内容会同步影响第三部分“土地级别”和第四部分“基准地价系数修正法”理由。</div>
            </div>
            <div class="base-price-elapsed">{{ basePriceElapsedYearsLabel }}</div>
          </div>

          <div class="base-price-grid">
            <div class="form-item" id="focus_item_base_price_drawer_base_price_doc_name">
              <label class="form-label">基准地价文件名称（base_price_doc_name）</label>
              <input type="text" v-model="form.base_price_doc_name.value" @input="onFieldInput('base_price_doc_name')" :class="['field-input', getInputClass('base_price_doc_name'), { 'flicker-glow-active': activeFlickerField === 'base_price_doc_name' }]" placeholder="如：《关于更新城区基准地价和制订11个建制镇基准地价的通告》" />
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_doc_no">
              <label class="form-label">批准/发布文号（base_price_doc_no）</label>
              <input type="text" v-model="form.base_price_doc_no.value" @input="onFieldInput('base_price_doc_no')" :class="['field-input', getInputClass('base_price_doc_no'), { 'flicker-glow-active': activeFlickerField === 'base_price_doc_no' }]" placeholder="如：道政函〔2019〕85号" />
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_doc_authority">
              <label class="form-label">批准/发布机关（base_price_doc_authority）</label>
              <input type="text" v-model="form.base_price_doc_authority.value" @input="onFieldInput('base_price_doc_authority')" :class="['field-input', getInputClass('base_price_doc_authority'), { 'flicker-glow-active': activeFlickerField === 'base_price_doc_authority' }]" placeholder="如：通道县自然资源局" />
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_publish_date">
              <label class="form-label">颁布实施日期（base_price_publish_date）</label>
              <input type="text" v-model="form.base_price_publish_date.value" @input="onFieldInput('base_price_publish_date')" :class="['field-input', getInputClass('base_price_publish_date'), { 'flicker-glow-active': activeFlickerField === 'base_price_publish_date' }]" placeholder="如：2019年11月22日" />
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_base_date">
              <label class="form-label">估价基准日（base_price_base_date）</label>
              <input type="text" v-model="form.base_price_base_date.value" @input="onFieldInput('base_price_base_date')" :class="['field-input', getInputClass('base_price_base_date'), { 'flicker-glow-active': activeFlickerField === 'base_price_base_date' }]" placeholder="如：2019年5月1日" />
            </div>
            <div class="form-item">
              <label class="form-label">基准地价时效判断</label>
              <div class="base-price-switch-row">
                <span>{{ basePriceExpiryStatusText }}</span>
              </div>
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_rule_doc_name">
              <label class="form-label">更新管理依据文件</label>
              <input type="text" v-model="form.base_price_rule_doc_name.value" @input="onFieldInput('base_price_rule_doc_name')" :class="['field-input', getInputClass('base_price_rule_doc_name'), { 'flicker-glow-active': activeFlickerField === 'base_price_rule_doc_name' }]" />
              <div class="basis-reference-actions"><select class="field-input" @change="e => { if (e.target.value) { form.base_price_rule_doc_name.value = e.target.value; onFieldInput('base_price_rule_doc_name'); e.target.value = '' } }"><option value="">引用已有依据</option><option v-for="option in sharedBasisReferenceOptions" :key="`base_rule_${option}`" :value="option">{{ option }}</option></select><button class="table-action inline-mini" @click="addSharedValuationBasis(form.base_price_rule_doc_name.value)">加入共享清单</button></div>
            </div>
            <div class="form-item" id="focus_item_base_price_drawer_base_price_rule_doc_no">
              <label class="form-label">更新管理依据文号</label>
              <input type="text" v-model="form.base_price_rule_doc_no.value" @input="onFieldInput('base_price_rule_doc_no')" :class="['field-input', getInputClass('base_price_rule_doc_no'), { 'flicker-glow-active': activeFlickerField === 'base_price_rule_doc_no' }]" />
            </div>
          </div>
        </div>
      </div>

      <div class="ocr-drawer" :class="{ 'drawer-open': showOCR }">
        <div class="drawer-header">
          <h2>📎 OCR 证据池</h2>
          <div class="drawer-actions">
            <button class="icon-btn danger" @click="showOCR = false">✖ 关闭</button>
          </div>
        </div>
        <div class="ocr-drawer-body">
          <section class="ocr-terminal-bar">
            <div class="terminal-title">
              <span>📷 附件识别与文本快速离线提取终端</span>
              <span style="font-size: 11px; color: var(--accent); font-weight: normal;">PDF/Word 文字层本地提取</span>
            </div>
            
            <textarea v-model="ocrRawText" class="ocr-textarea" 
                      placeholder="可直接上传 PDF/Word/txt 附件，也可在此粘贴不动产权证、国有土地使用证、规划条件函或基准地价报告的原始文本。PDF 文字层过少或上传图片时，将在已安装 PaddleOCR 的情况下自动唤醒 OCR。"></textarea>
            
            <div class="terminal-controls">
              <select v-model="ocrType" class="terminal-select">
                <option value="property_cert">📁 提取不动产权证指标</option>
                <option value="planning_condition">📐 提取规划条件函指标</option>
                <option value="base_price_report">🗺️ 提取基准地价报告资料</option>
              </select>

              <input type="number"
                     v-model.number="ocrMinTextChars"
                     min="0"
                     class="terminal-select"
                     style="max-width: 118px;"
                     title="PDF文字层少于该字数时自动唤醒PaddleOCR"
                     placeholder="文字阈值" />

              <input type="file"
                     multiple
                     class="terminal-select"
                     style="max-width: 240px;"
                     accept=".pdf,.docx,.txt,.text,.md,.png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp"
                     @change="handleOcrFileUpload" />
              
              <button class="icon-btn primary" @click="handleOcrExtract" :disabled="isLoading">
                <span>🚀 智能识别指标</span>
              </button>
            </div>
          </section>

          <div v-if="ocrEvidencePool.length > 0" class="evidence-pool">
            <div class="evidence-pool-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <span class="evidence-title" style="margin: 0; font-size: 13px; font-weight: 700;">📋 智能提取比对池 ({{ ocrEvidencePool.length }}项)</span>
              <div class="bulk-actions" style="display: flex; gap: 8px;">
                <button class="icon-btn" style="font-size: 11px; padding: 4px 8px; height: auto;" @click="toggleSelectAll(true)">全选</button>
                <button class="icon-btn" style="font-size: 11px; padding: 4px 8px; height: auto;" @click="toggleSelectAll(false)">全清</button>
              </div>
            </div>

            <div class="pending-injection-list">
              <div v-for="(item, idx) in ocrEvidencePool" :key="item.id" class="injection-compare-card" :class="{ 'has-conflict': hasConflict(item) }">
                <div class="card-top">
                  <label class="compare-checkbox-label">
                    <input type="checkbox" v-model="item.checked" class="compare-checkbox" />
                    <span class="compare-field-label">{{ item.label }}</span>
                  </label>
                  <span class="compare-field-key">({{ item.field }})</span>
                </div>
                
                <div class="compare-content">
                  <div class="compare-box old">
                    <span class="box-tag">当前表单值</span>
                    <span class="box-val">{{ hasOldValue(item.oldValue) ? item.oldValue : '（空值）' }}</span>
                  </div>
                  <div class="compare-arrow">→</div>
                  <div class="compare-box new">
                    <span class="box-tag">提取候选新值</span>
                    <span class="box-val">{{ item.value }}</span>
                  </div>
                </div>

                <div v-if="hasConflict(item)" class="conflict-warning-tip">
                  ⚠️ 警告：该字段已有{{ item.isDirty ? '人工修改' : '非空旧值' }}，覆盖可能有风险。
                </div>

                <!-- 📁 V6.2 附件文件名源展示与智能清洗置顶回填 -->
                <div v-if="item.fileName" class="fileName-fill-bar" style="margin-top: 4px; padding: 6px 8px; background: rgba(255,255,255,0.05); border-radius: 4px; font-size: 11px; display: flex; justify-content: space-between; align-items: center; border: 1px dashed rgba(14, 165, 233, 0.3);">
                  <span style="color: var(--text-secondary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 280px;" :title="item.fileName">📁 来源附件: {{ item.fileName }}</span>
                  <button class="action-link primary-link" style="padding: 0; font-size: 11px;" @click="applyFileNameToField(idx)" title="将清洗后的附件文件名追加到依据文件清单">
                    📄 加入依据
                  </button>
                </div>

                <div class="compare-actions-row">
                  <button v-if="isBasisDocCandidate(item)" class="action-link primary-link" @click="injectEvidenceToBasisDocs(idx)" title="追加到第三章权属依据清单中">
                    📄 依据注入
                  </button>
                  <span v-if="isBasisDocCandidate(item)" class="divider">|</span>
                  <button class="action-link" @click="applyEvidenceToField(idx)" title="强制直接写入此字段并亮蓝色高亮">
                    ⚡ 单项覆盖
                  </button>
                  <span class="divider">|</span>
                  <button class="action-link danger-link" @click="discardEvidence(idx)">
                    忽略
                  </button>
                </div>
              </div>
            </div>

            <div class="bulk-footer-actions" style="margin-top: 16px; display: grid; grid-template-columns: 2fr 1fr; gap: 8px;">
              <button class="icon-btn primary" style="justify-content: center; font-weight: 700; height: 36px;" @click="applyBulkOcrInjections">
                ⚡ 一键覆盖注入选中的表单
              </button>
              <button class="icon-btn danger" style="justify-content: center; height: 36px;" @click="ocrEvidencePool = []">
                全部清空
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- ==============================================================================
           右侧：A4 比例 1:1 高保真PDF 预览
           ============================================================================== -->
      
      <div class="preview-drawer" :class="{ 'drawer-open': showPreview }">
        <div class="drawer-header">
          <h2>📄 A4 高保真预览区</h2>
          <div class="drawer-actions">
            <button class="icon-btn" @click="handleRenderReport" :disabled="isLoading">刷新渲染</button>
            <button class="icon-btn primary" @click="downloadWordReport()" :disabled="isLoading">下载 Word</button>
            <a v-if="wordDownloadUrl" :href="wordDownloadUrl" :download="wordDownloadFileName" class="icon-btn">重新下载 Word</a>
            <button class="icon-btn danger" @click="showPreview = false">✖ 关闭</button>
          </div>
        </div>
        <section class="right-panel">

        
        <!-- PDF A4 比例预览面板 -->
        <div class="a4-preview-board">
          <template v-if="pdfUrl">
            <!-- 如果是高保真 PDF 物理流，正常 iframe 预览 -->
            <iframe v-if="pdfUrlType === 'pdf'" :src="pdfUrl" class="a4-preview-iframe"></iframe>
            
            <!-- 如果是降级 Word 物理流，显示 Premium 极光交互大卡片，彻底消灭预览空白！ -->
            <div v-else-if="pdfUrlType === 'docx'" class="preview-placeholder" style="background-color: #0f172a; padding: 20px; flex-direction: column;">
              <div class="word-card-container">
                <div class="word-icon">📥</div>
                <h3 class="word-title">高保真Word 报告极速生成成鍔燂紒</h3>
                <p class="word-desc">
                  鉴于本地 Word 物理另存为接口挂起，为了不影响您的测试节奏，平台已<b>自动降级自愈并触发浏览器极速下载</b>！<br>
                  高保真 Word 文件已在本地安全物理归档并下载，您可以立刻打开测试。
                </p>
                
                <div style="display: flex; gap: 12px; justify-content: center; width: 100%;">
                  <a :href="pdfUrl" download="重新下载高保真报告docx" class="aurora-glow-button" style="text-decoration: none; width: 100%; justify-content: center;">
                    <span>重新下载 Word 报告</span>
                  </a>
                </div>
              </div>
            </div>
          </template>
          
          <!-- 引导页遮罩-->
          <div v-else class="preview-placeholder">
            <div class="placeholder-icon">📄</div>
            <h3 class="placeholder-title">高保真A4 报告预览监视器</h3>
            <p class="placeholder-desc">
              暂无当前渲染快照。请通过左侧导入 Excel 测算表或提取证照指标，确认无误后点击右上角<b>“高保真 A4 渲染”</b>。
            </p>
            <p style="font-size: 11px; color: var(--text-secondary);">
              转换将物理调用本地 Word 引擎，生成后通过 <b>BackgroundTasks</b> 自动完成即用即销清理，不占用额外磁盘！
            </p>
          </div>
        </div>
        
        <!-- 🌀 API 加载中遮罩 -->
        <div v-if="isLoading" class="loading-overlay">
          <div class="spinner"></div>
          <div style="color: #ffffff; font-size: 14px; font-weight: 600;">{{ loadingMessage }}</div>
        </div>
        
      </section>
      </div>
    </main>
    
    <!-- 🔔 全局 Toast 通知 -->
    <div class="toast-container">
      <div v-for="toast in toasts" :key="toast.id" :class="['toast', toast.type]">
        <span>{{ toast.text }}</span>
      </div>
    </div>

    <!-- 💡 V6.2 伴生气泡悬浮 Tooltip 卡片 -->
    <div v-if="tooltipState.show" 
         class="aurora-tooltip" 
         :style="{ top: tooltipState.y + 'px', left: tooltipState.x + 'px' }"
         style="position: fixed; z-index: 9999; transform: translate(-50%, -120%); background: rgba(15, 23, 42, 0.95); border: 1px solid var(--accent); border-radius: 6px; padding: 6px 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.4); font-size: 11px; pointer-events: none; backdrop-filter: blur(10px); transition: top 0.08s, left 0.08s;">
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 2px;">{{ tooltipState.title }}</div>
      <div style="color: var(--text-secondary);">源自元素: <code style="color: #f8fafc;">{{ tooltipState.field }}</code></div>
    </div>

    <!-- 📋 表3-1 从政策目录添加补偿项目 -->
    <div v-if="costBuildingAddOpen" class="missing-fields-modal-overlay" @click.self="costBuildingAddOpen = false">
      <div class="missing-fields-modal cost-policy-help-modal cost-building-add-modal">
        <div class="modal-header">
          <span class="modal-title">从{{ costBuildingPolicyHelp.policy_document_no || '政策' }} 目录添加补偿项目</span>
          <button class="close-btn" type="button" @click="costBuildingAddOpen = false">✖</button>
        </div>
        <div class="modal-body">
          <p v-if="costBuildingPolicyHelp.policy_name" class="muted-text">{{ costBuildingPolicyHelp.policy_name }}（{{ costBuildingPolicyHelp.policy_document_no }}）</p>
          <p v-if="costBuildingAddLoading" class="muted-text">正在加载政策目录…</p>
          <div v-else class="table-scroll">
            <table class="comparable-table cost-help-table cost-building-add-table">
              <thead><tr><th>选择</th><th>补偿项目</th><th>结构/级别</th><th>标准</th><th>计算基数</th><th>政策说明</th></tr></thead>
              <tbody>
                <tr
                  v-for="entry in costBuildingAddCatalog"
                  :key="entry.row_key"
                  :class="{ 'cost-row-disabled': costBuildingExistingRowKeys.has(entry.row_key), 'cost-row-selected': costBuildingAddDraft.rowKey === entry.row_key }"
                  @click="!costBuildingExistingRowKeys.has(entry.row_key) && (costBuildingAddDraft.rowKey = entry.row_key, costBuildingAddDraft.gradeKey = entry.grade_options?.find(o => o.is_default)?.key || entry.grade_options?.[0]?.key || '')"
                >
                  <td>
                    <input type="radio" name="cost-building-add-row" :value="entry.row_key" v-model="costBuildingAddDraft.rowKey" :disabled="costBuildingExistingRowKeys.has(entry.row_key)" />
                  </td>
                  <td><strong>{{ entry.label }}</strong><small v-if="costBuildingExistingRowKeys.has(entry.row_key)" class="muted-text"> · 已在表中</small></td>
                  <td>
                    <select v-if="(entry.grade_options || []).length && costBuildingAddDraft.rowKey === entry.row_key && !costBuildingExistingRowKeys.has(entry.row_key)" v-model="costBuildingAddDraft.gradeKey" class="field-input compact-input" @click.stop>
                      <option v-for="option in entry.grade_options" :key="option.key" :value="option.key">{{ option.label }}</option>
                    </select>
                    <span v-else-if="(entry.grade_options || []).length">{{ (entry.grade_options.find(o => o.is_default) || entry.grade_options[0])?.label || '-' }}</span>
                    <span v-else class="cost-na-chip">固定标准</span>
                  </td>
                  <td>{{ costBuildingAddPreview(entry).standard }} {{ entry.template?.standard_unit || '元/平方米' }}</td>
                  <td>{{ entry.template?.calculation_basis || '-' }}</td>
                  <td>{{ costBuildingAddPreview(entry).note || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button class="icon-btn" type="button" @click="costBuildingAddOpen = false">取消</button>
          <button class="icon-btn primary" type="button" :disabled="!costBuildingAddDraft.rowKey || costBuildingExistingRowKeys.has(costBuildingAddDraft.rowKey)" @click="confirmCostBuildingAddRow">添加所选项目</button>
        </div>
      </div>
    </div>

    <!-- 成本逼近法调价助手悬浮窗 -->
    <div
      v-if="costPricingAssistantOpen"
      class="cost-pricing-assistant"
      :style="costPricingAssistantStyle"
      role="dialog"
      aria-label="成本逼近法调价助手"
    >
      <header class="cost-pricing-assistant-header" @mousedown="startCostPricingDrag">
        <div><strong>调价助手</strong><small>试算沙盒 · 拖动标题栏 · 改等级或数值即时重算 · 确认后应用到主表</small></div>
        <button class="close-btn" type="button" aria-label="关闭调价助手" @click="costPricingAssistantOpen = false">✖</button>
      </header>
      <div class="cost-pricing-assistant-body">
        <p v-if="costPricingLoading" class="muted-text">正在计算并加载可调项…</p>
        <p v-else-if="!costPricingControls.length" class="muted-text">暂无可调项。请确认已填写县市、征收地类，并点击「计算并校核」。</p>
        <label class="cost-pricing-field">
          <span>组合方案</span>
          <select v-model="costPricingScenarioKey" class="field-input" @change="applyCostPricingScenario(costPricingScenarioKey)">
            <option v-if="costPricingScenarioKey === 'custom'" value="custom">当前试算（自定义调整）</option>
            <option v-for="scenario in costPricingScenarios" :key="scenario.key" :value="scenario.key">
              {{ scenario.label }} — {{ scenario.final_price || '待计算' }} 元/㎡
            </option>
          </select>
        </label>
        <div class="cost-pricing-formula">
          <span v-for="(part, index) in costPricingFormulaParts" :key="part.key">
            <span v-if="index"> + </span>
            <span :class="{ 'cost-pricing-changed': isCostPricingChanged(part.key) }">{{ part.label }} {{ part.value }}</span>
          </span>
          <span> ⇒ 成本价{{ costPricingPreviewCostPrice || '-' }} ⇒ 最终{{ costPricingPreviewFinalPrice || '-' }} 元/㎡</span>
        </div>
        <div class="cost-pricing-controls">
          <div v-for="control in costPricingControls" :key="`${control.key}-${control.value}-${control.amount_per_sqm}`" class="cost-pricing-control-row">
            <span class="cost-pricing-control-label" :class="{ 'cost-pricing-changed': isCostPricingChanged(control.key) }">{{ control.label }}</span>
            <select v-if="control.type === 'grade'" :value="control.value" class="field-input compact-input" @change="onCostPricingControlChange(control, $event)">
              <option value="">请选择</option>
              <option v-for="option in control.options" :key="option" :value="option">{{ option }}</option>
            </select>
            <input v-else :value="control.value" class="field-input compact-input" @change="onCostPricingControlChange(control, $event)" />
            <small>{{ control.amount_per_sqm || '-' }} 元/㎡</small>
          </div>
        </div>
        <ul v-if="costPricingChangedItems.length" class="cost-pricing-changes">
          <li v-for="item in costPricingChangedItems" :key="item.key">{{ item.label }}：{{ item.from }} → {{ item.to }}</li>
        </ul>
        <div class="cost-pricing-entry-points">
          <button class="table-action primary-action" type="button" :disabled="costPricingLoading" @click="applyCostPricingToMain">应用到主表</button>
          <button v-for="entry in costPricingEntryPoints" :key="entry.key" class="table-action" type="button" @click="openCostPricingEntryPoint(entry)">{{ entry.label }}</button>
        </div>
      </div>
    </div>

    <!-- 📋 表3-1/3-2 建筑物补偿测算说明 -->
    <div v-if="costBuildingHelpOpen" class="missing-fields-modal-overlay" @click.self="costBuildingHelpOpen = false">
      <div class="missing-fields-modal cost-policy-help-modal">
        <div class="modal-header">
          <span class="modal-title">{{ costBuildingPolicyHelp.policy_document_no || '建筑物补偿' }} 政策标准一览</span>
          <button class="close-btn" type="button" @click="costBuildingHelpOpen = false">✖</button>
        </div>
        <div class="modal-body">
          <p v-if="costBuildingPolicyHelp.policy_name" class="muted-text">{{ costBuildingPolicyHelp.policy_name }}（{{ costBuildingPolicyHelp.policy_document_no }}）</p>
          <p v-else class="muted-text">当前县市暂未结构化本地建筑物补偿政策，下列为表单已配置项目；完整标准请对照政策原件。</p>
          <div class="table-scroll">
            <table class="comparable-table cost-derived-table cost-help-table">
              <thead><tr><th>补偿项目</th><th>级别/口径</th><th>标准值</th><th>单位</th><th>说明</th></tr></thead>
              <tbody>
                <template v-for="group in costBuildingPolicyHelpGroups" :key="group.label">
                  <tr v-for="(entry, rowIndex) in group.rows" :key="entry.option_key || entry.row_key || rowIndex">
                    <td v-if="rowIndex === 0" :rowspan="group.rows.length" class="cost-help-group-cell">{{ group.label }}</td>
                    <td>{{ entry.label && entry.label !== group.label ? entry.label : '-' }}</td>
                    <td>{{ entry.standard || '-' }}</td>
                    <td>{{ entry.standard_unit || '-' }}</td>
                    <td>{{ entry.note || '-' }}</td>
                  </tr>
                </template>
                <tr v-if="!costBuildingPolicyHelpGroups.length">
                  <td colspan="5" class="muted-text">当前县市暂无结构化建筑物补偿标准。</td>
                </tr>
              </tbody>
            </table>
          </div>
          <h4 class="cost-help-section-title">新增建设用地有偿使用费（湘财综〔2018〕42号 附件1）</h4>
          <div class="table-scroll">
            <table class="comparable-table cost-derived-table cost-help-table">
              <thead><tr><th>等别</th><th>标准值</th><th>单位</th><th>说明</th></tr></thead>
              <tbody>
                <tr v-for="entry in costBuildingPolicyHelp.paid_land_use_fee_standards || []" :key="entry.label">
                  <td>{{ entry.label }}</td>
                  <td>{{ entry.standard }}</td>
                  <td>{{ entry.standard_unit }}</td>
                  <td>{{ entry.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <details class="cost-help-formula-block">
            <summary>测算公式说明</summary>
            <p>表3-1 行金额 = 标准 × 数量 × 月数 ÷ 除数；合计为<strong>元/人</strong>。</p>
            <p>表3-2 折算：<code>元/㎡ = 元/人 × 人/公顷 ÷ 10000</code>。</p>
          </details>
        </div>
        <div class="modal-footer">
          <button class="icon-btn primary" type="button" @click="costBuildingHelpOpen = false">知道了</button>
        </div>
      </div>
    </div>

    <!-- 📋 正式归档缺失核心要素检查清单弹窗 -->
    <div v-if="isMissingFieldsDialogOpen" class="missing-fields-modal-overlay">
      <div class="missing-fields-modal">
        <div class="modal-header">
          <span class="modal-title">⚠️ 正式归档核心要素缺失清单</span>
          <button class="close-btn" @click="isMissingFieldsDialogOpen = false">✖</button>
        </div>
        <div class="modal-body">
          <p class="modal-intro">
            检测到以下核心要素未填写或含有未填写占位符，正式归档需要补齐这些字段。请点击下方字段直接跳转至对应位置修改：
          </p>
          <div class="missing-fields-list">
            <div v-for="item in missingFields" :key="item.key" 
                 class="missing-field-item" 
                 @click="scrollToField(item.key)"
                 title="点击直接跳转并高亮此输入框">
              <span class="field-icon">📍</span>
              <span class="field-label">{{ item.label }}</span>
              <span class="field-key">({{ item.key }})</span>
              <span class="go-modify-link">去修改 ➜</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="icon-btn primary" style="width: 100%; justify-content: center; height: 36px;" @click="isMissingFieldsDialogOpen = false">
            好的，我去修改
          </button>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue';

// 1. 界面与主题控制
const isLightTheme = ref(false);
const isLoading = ref(false);
const loadingMessage = ref('加载中..');
const isDragging = ref(false);
const pdfUrl = ref('');
const pdfUrlType = ref('pdf'); // 可为 'pdf' 或 'docx'
const wordDownloadUrl = ref('');
const wordDownloadFileName = ref('');

const missingFields = ref([]);
const isMissingFieldsDialogOpen = ref(false);

// Excel 溯源元数据
const excelMetadata = reactive({
  name: '',
  md5: ''
});

// 折叠状态控制
const activeTab = ref('p1');
const showPreview = ref(false);
const showOCR = ref(false);
const showBasePriceDrawer = ref(false);
const ocrEvidencePool = ref([]);
const uploadedAttachments = ref([]);

const method_warnings = ref([]);
const method_warning_acknowledged = ref({});
const comparableViews = [
  { key: 'crawl', label: '数据抓取' },
  { key: 'library', label: '案例检索与选取' },
  { key: 'schemes', label: '规则管理' }
];
const marketWorkspaceViews = [
  { key: 'instances', label: '实例与参数' },
  { key: 'factors', label: '因素确认' },
  { key: 'narratives', label: '正文与表格' }
];
const costWorkspaceViews = [
  { key: 'policy', label: '政策与征收地类' },
  { key: 'costs', label: '费用测算' },
  { key: 'adjustments', label: '年期与区位修正' },
  { key: 'narratives', label: '正文与表格' }
];
const incomeWorkspaceViews = [
  { key: 'instances', label: '房屋与租金实例' },
  { key: 'factors', label: '租金因素确认' },
  { key: 'parameters', label: '收入费用与还原率' },
  { key: 'narratives', label: '正文与表格' }
];
const benchmarkWorkspaceViews = [
  { key: 'base', label: '适用性与级别' },
  { key: 'factors', label: '区域因素' },
  { key: 'corrections', label: '年期/容积率期日/个别修正' },
  { key: 'narratives', label: '正文与表格' }
];
const rentalUsageOptions = [
  { key: 'residential', label: '住宅' },
  { key: 'commercial', label: '商业' },
  { key: 'office', label: '办公' },
  { key: 'industrial', label: '工业' },
  { key: 'warehouse', label: '仓储' },
  { key: 'other', label: '其他' }
];
const rentalUsageByKey = Object.fromEntries(rentalUsageOptions.map(item => [item.key, item]));
const incomeRentFactorScales = {
  usage: { scaleType: 'equality', values: [], step: 0, defaultValue: '' },
  transaction_time: { scaleType: 'equality_month', values: [], step: 0, defaultValue: '' },
  transaction_condition: { scaleType: 'equality', values: ['正常交易', '非正常交易'], step: 0, defaultValue: '正常交易' },
  commercial_prosperity: { scaleType: 'ordered', values: ['优', '较优', '一般', '较劣', '劣'], step: 2, defaultValue: '较优' },
  bus_convenience: { scaleType: 'ordered', values: ['优', '较优', '一般', '较劣', '劣'], step: 2, defaultValue: '较优' },
  road_accessibility: { scaleType: 'ordered', values: ['通畅', '较通畅', '一般通畅', '较不通畅', '不通畅'], step: 2, defaultValue: '较通畅' },
  infrastructure_guarantee: { scaleType: 'ordered', values: ['≥95%', '90%-<95%', '<90%'], step: 2, defaultValue: '≥95%' },
  environment_quality: { scaleType: 'ordered', values: ['好', '较好', '一般', '较差', '差'], step: 2, defaultValue: '好' },
  public_facilities: { scaleType: 'ordered', values: ['齐全', '较齐全', '一般', '较低', '低'], step: 2, defaultValue: '齐全' },
  road_type: { scaleType: 'ordered', values: ['临主干道', '临次干道', '临支路', '不临路'], step: 1, defaultValue: '临主干道' },
  ventilation_lighting: { scaleType: 'ordered', values: ['好', '较好', '一般', '较差', '差'], step: 1, defaultValue: '好' },
  newness: { scaleType: 'ordered', values: ['十成新', '九成新', '八成新', '七成新', '六成新', '五成新', '四成新', '三成新', '二成新', '一成新'], step: 4, defaultValue: '七成新' },
  building_structure: { scaleType: 'ordered', values: ['框架', '钢混', '砖混', '砖木'], step: 2, defaultValue: '砖混' },
  internal_layout: { scaleType: 'ordered', values: ['合理', '较合理', '不合理'], step: 1, defaultValue: '合理' },
  decoration: { scaleType: 'ordered', values: ['高档', '中高档', '中档', '简单装修', '毛坯'], step: 2, defaultValue: '简单装修' },
  parking: { scaleType: 'ordered', values: ['能满足停车需求', '基本满足停车需求', '不能满足停车需求'], step: 2, defaultValue: '基本满足停车需求' },
  property_management: { scaleType: 'ordered', values: ['物业管理较好', '物业管理一般', '无物业管理'], step: 2, defaultValue: '无物业管理' }
};
const incomeFactorValueAliases = {
  '95%': '≥95%',
  '大于等于95%': '≥95%',
  '框架结构': '框架',
  '钢混结构': '钢混',
  '砖混结构': '砖混',
  '砖木结构': '砖木',
  '能满足停车': '能满足停车需求',
  '基本满足停车': '基本满足停车需求',
  '不能满足停车': '不能满足停车需求',
  '无': '无物业管理'
};
const genericIncomeFactorLevels = ['优', '较优', '一般', '较劣', '劣'];
const residentialConstructionCostStandards = [
  { key: 'steel_concrete_1', structureKey: 'steel_concrete', structure: '钢混结构', gradeKey: '1', grade: '一等', min: '2300', max: '2500' },
  { key: 'steel_concrete_2', structureKey: 'steel_concrete', structure: '钢混结构', gradeKey: '2', grade: '二等', min: '1900', max: '2100' },
  { key: 'steel_concrete_3', structureKey: 'steel_concrete', structure: '钢混结构', gradeKey: '3', grade: '三等', min: '1700', max: '1900' },
  { key: 'steel_concrete_4', structureKey: 'steel_concrete', structure: '钢混结构', gradeKey: '4', grade: '四等', min: '1500', max: '1700' },
  { key: 'brick_concrete_1', structureKey: 'brick_concrete', structure: '砖混结构', gradeKey: '1', grade: '一等', min: '1300', max: '1400' },
  { key: 'brick_concrete_2', structureKey: 'brick_concrete', structure: '砖混结构', gradeKey: '2', grade: '二等', min: '1200', max: '1300' },
  { key: 'brick_wood', structureKey: 'brick_wood', structure: '砖木结构', gradeKey: '', grade: '/', min: '900', max: '1000' },
  { key: 'simple', structureKey: 'simple', structure: '简易结构', gradeKey: '', grade: '/', min: '350', max: '500' }
];
const residentialConstructionCostByKey = Object.fromEntries(residentialConstructionCostStandards.map(item => [item.key, item]));
const residentialStructureOptions = [
  { key: 'steel_concrete', label: '钢混结构' },
  { key: 'brick_concrete', label: '砖混结构' },
  { key: 'brick_wood', label: '砖木结构' },
  { key: 'simple', label: '简易结构' }
];
const costFlowAnchors = [
  { id: 'cost-section-population', label: '① 表3-2 人口' },
  { id: 'cost-section-building', label: '② 表3-1 建筑物' },
  { id: 'cost-section-acquisition', label: '③ 取得费汇总' },
  { id: 'cost-section-tax', label: '④ 税费' },
  { id: 'cost-section-development', label: '⑤ 开发费' },
];

const scrollToCostSection = (sectionId) => {
  costWorkspaceView.value = 'costs';
  nextTick(() => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
};

const costItemGroups = [
  { key: 'acquisition_items', label: '土地取得费' }
];
const costPostAttachmentItemGroups = [
  { key: 'tax_items', label: '相关税费' }
];
const acquisitionLandClassTree = {
  '耕地': ['水田', '水浇地', '旱地'],
  '园地': ['果园', '茶园', '其他园地'],
  '林地': ['乔木林地', '竹林地', '灌木林地', '其他林地'],
  '草地': ['天然牧草地', '人工牧草地', '其他草地'],
  '其他农用地': ['设施农用地', '农村道路', '坑塘水面', '沟渠', '其他']
};
const acquisitionLandSubclassOptions = computed(() => (
  acquisitionLandClassTree[form.acquisition_land_class?.value] || acquisitionLandClassTree['耕地']
));
const comparableView = ref('library');
const marketWorkspaceView = ref('instances');
const costWorkspaceView = ref('policy');
const costShowDevelopmentSurvey = false;
const costBuildingHelpOpen = ref(false);
const costPricingAssistantOpen = ref(false);
const costPricingScenarioKey = ref('current');
const costPricingChangedKeys = ref([]);
const costPricingAssistantPos = ref({ x: null, y: null });
const costPricingDragState = ref(null);

const costPricingAssistantStyle = computed(() => {
  if (costPricingAssistantPos.value.x == null || costPricingAssistantPos.value.y == null) return {};
  return {
    left: `${costPricingAssistantPos.value.x}px`,
    top: `${costPricingAssistantPos.value.y}px`,
    right: 'auto',
    bottom: 'auto',
  };
});

const startCostPricingDrag = (event) => {
  if (event.target.closest('button')) return;
  const panel = event.currentTarget?.closest('.cost-pricing-assistant');
  if (!panel) return;
  const rect = panel.getBoundingClientRect();
  if (costPricingAssistantPos.value.x == null) {
    costPricingAssistantPos.value = { x: rect.left, y: rect.top };
  }
  costPricingDragState.value = {
    startX: event.clientX,
    startY: event.clientY,
    originX: costPricingAssistantPos.value.x,
    originY: costPricingAssistantPos.value.y,
  };
  const onMove = (moveEvent) => {
    if (!costPricingDragState.value) return;
    costPricingAssistantPos.value = {
      x: Math.max(8, costPricingDragState.value.originX + moveEvent.clientX - costPricingDragState.value.startX),
      y: Math.max(8, costPricingDragState.value.originY + moveEvent.clientY - costPricingDragState.value.startY),
    };
  };
  const onUp = () => {
    costPricingDragState.value = null;
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
  };
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
};
const incomeWorkspaceView = ref('instances');
const costAnalysis = ref({
  compensation_zone: 'Ⅰ',
  compensation_zone_override: false,
  compensation_zone_suggestion: {},
  location_correction_mode: 'direct_sum',
  location_template_key: '',
  risk_mode: 'direct',
  policy_documents: [],
  acquisition_items: [],
  tax_items: [],
  development_items: [],
  development_survey_cases: [],
  development_survey_analysis: {},
  usage_scenarios: [],
  usage_results: [],
  risk_items: [],
  risk_groups: [],
  location_factors: [],
  external_results: [],
  rounding_trace: []
});
const costNewLocationFactorGroup = ref('');
const costLocationFactorGroups = computed(() => {
  const groups = [];
  for (const factor of costAnalysis.value?.location_factors || []) {
    const group = String(factor.group || '').trim();
    if (group && !groups.includes(group)) groups.push(group);
  }
  if (!groups.length) groups.push('区域因素', '个别因素');
  return groups;
});
const costDeletedTemplateLocationFactors = computed(() => (
  (costAnalysis.value?.location_factors || []).filter(factor => factor?.enabled === false && !String(factor?.source || '').includes('manual'))
));
watch(costLocationFactorGroups, (groups) => {
  if (!costNewLocationFactorGroup.value && groups.length) costNewLocationFactorGroup.value = groups[0];
}, { immediate: true });
const latestLpr = ref(null);
const costPolicyDraft = ref({
  name: '',
  document_no: '',
  region: '湖南省',
  publish_date: '',
  effective_date: '',
  role: 'supplemental',
  source_type: 'manual',
  reference_text: '',
  replaces_key: '',
  note: ''
});
const incomeAnalysis = ref({
  rent_instances: [],
  rent_factor_items: [],
  building_profile: {},
  income_parameters: {},
  expense_parameters: {},
  cap_rate_parameters: {},
  rent_calculations: [],
  income_results: {}
});
const benchmarkWorkspaceView = ref('base');
const benchmarkAnalysis = ref({
  land_use_type: '',
  land_level: '',
  parameters: {},
  regional_factors: [],
  individual_factors: {},
  tables: {},
  results: {},
  benchmark_corr_price: ''
});
const marketFactorFilter = ref('all');
const incomeFactorFilter = ref('all');
const marketEvidenceKinds = [
  { key: 'announcement', label: '成交公告截图', field: 'market_comp_evidence_snapshot_ids', help: '上传官网供地结果信息截图' },
  { key: 'location', label: '位置图', field: 'market_comp_location_snapshot_ids', help: '上传比较实例位置图' },
  { key: 'site', label: '现状图', field: 'market_comp_site_snapshot_ids', help: '上传比较实例现状图' }
];
const comparableSlots = ['A', 'B', 'C'];
const crawlFilters = reactive({
  xzq_dm: '', start_date: '', end_date: '', land_usage_key: '', supply_method: '', location: '', electronic_supervision_no: '', refresh_complete_details: false
});
const libraryFilters = reactive({
  xzq_dm: '', land_usage_key: '', start_date: '', end_date: '', supply_method: '', location: '', electronic_supervision_no: '', keyword: ''
});
const crawlJob = ref(null);
const landChinaAccessStatus = ref(null);
const cloudProxyConfig = ref(null);
const cloudProxyForm = reactive({
  enabled: false,
  proxy_url: '',
  proxy_token: ''
});
let crawlPollTimer = null;
const comparableCases = ref([]);
const comparableTotal = ref(0);
const comparableRegionOptions = ref([]);
const selectedComparableIds = reactive({ A: '', B: '', C: '' });
const selectedComparableRecords = reactive({ A: null, B: null, C: null });
const editingComparableCase = ref(null);
const caseManualForm = ref({});
const caseChangedKeys = ref([]);
const caseAdvancedJson = ref('{}');
const caseFactorScheme = ref(null);
const caseDraftState = ref('');
let caseDraftSaveTimer = null;
const schemeUsageKey = ref('residential');
const factorScheme = ref(null);
const factorSchemeBaseline = ref(null);
const factorSchemeJson = ref('');
const showSchemeAdvanced = ref(false);
const showSchemeChangeDialog = ref(false);
const schemeChangeSummary = ref([]);
const activeFactorGuide = ref(null);
const factorGuideDirty = ref(false);
const factorGuideSnapshot = ref(null);
const marketAnalysis = ref(null);
const marketEvidenceSnapshots = ref([]);
const marketEvidenceDetails = reactive({
  announcement: { A: null, B: null, C: null },
  location: { A: null, B: null, C: null },
  site: { A: null, B: null, C: null }
});
const marketMonthlyGrowthRate = ref('0.13');
const marketLandReductionRate = ref('5.4');
const valuationProcessDraft = reactive({ methods: [] });
const activeProcessMethodKey = ref('');
const processViewMode = ref('edit');
const activeProcessMethod = computed(() => (
  valuationProcessDraft.methods.find(item => item.method_key === activeProcessMethodKey.value)
  || valuationProcessDraft.methods[0]
  || null
));
const costUsageResultPrices = computed(() => (
  (costAnalysis.value?.usage_results || []).filter(item => item?.final_price)
));
const costHasMultipleUsagePrices = computed(() => costUsageResultPrices.value.length > 1);

const comparableRegionCodeByName = {
  '道县': '431124',
  '湖南省永州市道县': '431124',
  '通道县': '431230',
  '通道侗族自治县': '431230',
  '湖南省怀化市通道县': '431230',
  '湖南省怀化市通道侗族自治县': '431230'
};

const defaultComparableRegionOptions = [
  { code: '431124', name: '湖南省永州市道县', count: 0 },
  { code: '431230', name: '湖南省怀化市通道侗族自治县', count: 0 }
];

const comparableManualCoreFields = [
  { key: 'transaction_condition', label: '交易情况', help: '正常交易、关联交易或其他特殊交易情况。' },
  { key: 'development_level', label: '开发程度', help: '填写交易时宗地红线内外实际开发程度。' },
  { key: 'parcel_shape', label: '宗地形状', help: '如规则、较规则、不规则。' },
  { key: 'terrain', label: '地势', help: '如平坦、较平坦、略有起伏。' },
  { key: 'geology', label: '地质条件', help: '如良好、一般、较差。' },
  { key: 'planning_restriction', label: '规划限制', help: '记录影响利用强度或开发条件的规划限制。' }
];

const comparableOfficialSummaryFields = [
  ['project_name', '项目名称'],
  ['location', '坐落'],
  ['land_usage_raw', '官网用途'],
  ['land_usage_first_level', '一级用途'],
  ['supply_method', '供应方式'],
  ['recipient', '土地使用权人'],
  ['area_sqm', '面积（㎡）'],
  ['unit_price_sqm', '地面单价（元/㎡）']
];

const caseGuidedFields = computed(() => {
  const seen = new Set();
  const fields = [];
  [...comparableManualCoreFields, ...(caseFactorScheme.value?.factors || [])
    .filter(item => item.source === 'manual' && item.group === '区域因素')
    .map(item => ({ key: item.key, label: item.label, help: item.help_text || item.note || '' }))]
    .forEach(item => {
      if (!seen.has(item.key)) {
        seen.add(item.key);
        fields.push(item);
      }
    });
  return fields;
});

const schemeFactorGroups = computed(() => {
  const groups = {};
  (factorScheme.value?.factors || []).forEach(factor => {
    const key = factor.group || '其他因素';
    if (!groups[key]) groups[key] = [];
    groups[key].push(factor);
  });
  return groups;
});

const marketAnalysisSummary = computed(() => {
  const factors = marketAnalysis.value?.factors || [];
  let total = 0;
  let confirmed = 0;
  factors.forEach(factor => comparableSlots.forEach(slot => {
    if (!factor.required) return;
    total += 1;
    if (factor.cases?.[slot]?.confirmed && String(factor.cases?.[slot]?.index || '').trim()) confirmed += 1;
  }));
  return {
    total,
    confirmed,
    missing: Math.max(total - confirmed, 0),
    percent: total ? Math.round(confirmed / total * 100) : 0
  };
});

const selectedComparableCount = computed(() => comparableSlots.filter(slot => selectedComparableIds[slot]).length);
const incomeRentInstanceCount = computed(() => (
  (incomeAnalysis.value?.rent_instances || []).filter(item => String(item.monthly_rent || '').trim()).length
));
const incomeImageCount = computed(() => (
  (incomeAnalysis.value?.rent_instances || []).reduce((total, item) => (
    total + (item.photo_data ? 1 : 0) + (item.location_image_data ? 1 : 0)
  ), 0)
));
const incomeFactorGroups = computed(() => {
  const groups = {};
  (incomeAnalysis.value?.rent_factor_items || []).forEach(factor => {
    const group = factor.group || '其他因素';
    if (!groups[group]) groups[group] = [];
    groups[group].push(factor);
  });
  return groups;
});
const visibleIncomeFactorGroups = computed(() => {
  if (incomeFactorFilter.value === 'all') return incomeFactorGroups.value;
  const groups = {};
  const targetGroup = incomeFactorFilter.value;
  if (incomeFactorGroups.value[targetGroup]) {
    groups[targetGroup] = incomeFactorGroups.value[targetGroup];
  }
  return groups;
});
const incomeFactorSummary = computed(() => {
  let total = 0;
  let confirmed = 0;
  (incomeAnalysis.value?.rent_factor_items || []).forEach(factor => comparableSlots.forEach(slot => {
    if (!factor.required) return;
    total += 1;
    if (factor.cases?.[slot]?.confirmed && String(factor.cases?.[slot]?.index || '').trim()) confirmed += 1;
  }));
  return {
    total,
    confirmed,
    percent: total ? Math.round(confirmed / total * 100) : 0
  };
});
const evidenceKindConfig = (kind) => marketEvidenceKinds.find(item => item.key === kind) || marketEvidenceKinds[0];
const evidenceFieldValue = (kind) => form[evidenceKindConfig(kind).field]?.value || [];
const evidenceCountFor = (kind) => comparableSlots.filter((slot, index) => evidenceFieldValue(kind)[index]).length;
const marketEvidenceCount = computed(() => evidenceCountFor('announcement'));
const marketMapPhotoCount = computed(() => evidenceCountFor('location') + evidenceCountFor('site'));
const marketSchemeName = computed(() => (
  marketAnalysis.value?.factor_scheme_snapshot?.name
  || marketAnalysis.value?.factor_scheme_name
  || '当前用途规则冻结快照'
));
const marketFactorGroups = computed(() => {
  const groups = {};
  (marketAnalysis.value?.factors || []).forEach(factor => {
    const group = factor.group || '其他因素';
    if (!groups[group]) groups[group] = [];
    groups[group].push(factor);
  });
  return groups;
});
const visibleMarketFactorGroups = computed(() => {
  if (marketFactorFilter.value === 'all') return marketFactorGroups.value;
  return Object.fromEntries(
    Object.entries(marketFactorGroups.value)
      .map(([group, factors]) => [group, factors.filter(factor => comparableSlots.some(slot => (
        !factor.cases?.[slot]?.confirmed || !String(factor.cases?.[slot]?.index || '').trim()
      )))])
      .filter(([, factors]) => factors.length)
  );
});
const activeFactorCanConfirm = computed(() => (
  activeFactorGuide.value
  && comparableSlots.every(slot => String(activeFactorGuide.value.factor.cases?.[slot]?.index || '').trim())
));
const marketComparableBasisStatus = computed({
  get: () => marketAnalysis.value?.comparable_basis_status || 'consistent',
  set: (value) => {
    const analysis = marketAnalysis.value || {};
    analysis.comparable_basis_status = value;
    marketAnalysis.value = analysis;
    form.market_comp_analysis.value = analysis;
  }
});
const marketNeedsTimeAdjustment = computed(() => {
  const valuationDate = String(marketAnalysis.value?.subject?.valuation_date || marketSubject().valuation_date || '');
  return comparableSlots.some(slot => {
    const caseDate = String(selectedComparableCase(slot)?.transaction_date || '');
    return valuationDate && caseDate && valuationDate !== caseDate;
  });
});
const marketNeedsTermAdjustment = computed(() => {
  const subjectYears = String(marketAnalysis.value?.subject?.land_use_term_years || marketSubject().land_use_term_years || '');
  return comparableSlots.some(slot => {
    const caseYears = String(selectedComparableCase(slot)?.use_term_years || '');
    return subjectYears && caseYears && subjectYears !== caseYears;
  });
});

watch(
  factorScheme,
  value => {
    if (value && !showSchemeAdvanced.value) {
      factorSchemeJson.value = JSON.stringify(value, null, 2);
    }
  },
  { deep: true }
);

const inferComparableXzqDm = (name) => {
  const text = String(name || '').trim();
  if (!text) return '';
  if (comparableRegionCodeByName[text]) return comparableRegionCodeByName[text];
  const match = Object.entries(comparableRegionCodeByName).find(([label]) => text.includes(label));
  return match ? match[1] : '';
};

const comparableRegionOptionLabel = (item) => {
  const name = item?.name || item?.code || '未命名行政区';
  const code = item?.code ? ` ${item.code}` : '';
  const count = item?.count ? `（${item.count}宗）` : '';
  return `${name}${code}${count}`;
};

const mergeComparableRegionOptions = (regions = []) => {
  const byCode = new Map();
  const addRegion = (region) => {
    const code = String(region?.code || region?.xzq_dm || '').trim();
    if (!code) return;
    const existing = byCode.get(code) || {};
    byCode.set(code, {
      code,
      name: String(region?.name || region?.label || existing.name || code).trim(),
      count: Number(region?.count ?? existing.count ?? 0) || 0
    });
  };
  defaultComparableRegionOptions.forEach(addRegion);
  const inferredCode = inferComparableXzqDm(form.county_name.value);
  if (inferredCode) addRegion({ code: inferredCode, name: form.county_name.value });
  regions.forEach(addRegion);
  return Array.from(byCode.values()).sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN'));
};

const isRegionNameLocationFilter = (location, xzqDm) => {
  const text = String(location || '').trim();
  if (!text || !xzqDm) return false;
  return inferComparableXzqDm(text) === String(xzqDm || '').trim();
};

const activeMethodWarnings = computed(() => {
  return method_warnings.value.filter(warn => {
    const key = warn.method + '_' + warn.message;
    return !method_warning_acknowledged.value[key];
  });
});

const parseCnDate = (value) => {
  const text = String(value || '').trim();
  let match = text.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?/);
  if (!match) match = text.match(/(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})/);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (!year || !month || !day) return null;
  return { year, month, day };
};

const cnNumber = (num) => {
  const digits = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  if (num < 10) return digits[num] || String(num);
  if (num < 20) return num === 10 ? '十' : `十${digits[num % 10]}`;
  if (num < 100) {
    const tens = Math.floor(num / 10);
    const ones = num % 10;
    return `${digits[tens]}十${ones ? digits[ones] : ''}`;
  }
  return String(num);
};

const yearsBetween = (later, earlier) => {
  if (!later || !earlier) return null;
  let years = later.year - earlier.year;
  if (later.month < earlier.month || (later.month === earlier.month && later.day < earlier.day)) {
    years -= 1;
  }
  return Math.max(years, 0);
};

const basePriceComparisonDate = computed(() => {
  return parseCnDate(form.base_price_base_date?.value) || parseCnDate(form.base_price_publish_date?.value);
});

const basePriceElapsedYears = computed(() => {
  return yearsBetween(parseCnDate(form.valuation_date?.value), basePriceComparisonDate.value);
});

const basePriceDisableThreshold = computed(() => {
  const text = String(form.base_price_disable_threshold_years_text?.value || '六').replace('年', '').trim();
  const numeric = Number(text);
  if (Number.isFinite(numeric) && numeric > 0) return numeric;
  const mapping = { 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10 };
  return mapping[text] || 6;
});

const basePriceElapsedYearsLabel = computed(() => {
  const years = basePriceElapsedYears.value;
  if (years === null) return '需填写估价期日与基准地价估价基准日后自动计算';
  return `距估价期日 ${years} 年（${cnNumber(years)}年）`;
});

const basePriceExpiryStatusText = computed(() => {
  const years = basePriceElapsedYears.value;
  if (years === null) return '待补充日期后判断';
  return years > basePriceDisableThreshold.value ? `系统判断：超过${cnNumber(basePriceDisableThreshold.value)}年` : `系统判断：未超过${cnNumber(basePriceDisableThreshold.value)}年`;
});

const FIELD_REGISTRY = {
  comparable_case_count: {
    label: '可比交易案例数量',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  case_similarity_level: {
    label: '案例可比性',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  case_time_valid: {
    label: '案例交易时间是否合理',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  market_activity_level: {
    label: '同类用地市场活跃程度',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  has_stable_income_data: {
    label: '具备稳定收益或租金资料',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  income_can_be_separated: {
    label: '土地纯收益可从混合收益中合理剥离',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  rent_market_activity_level: {
    label: '租赁市场活跃程度',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cap_rate_source_available: {
    label: '还原率来源可靠',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  has_development_plan: {
    label: '具备明确开发或再开发方案',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  development_value_measurable: {
    label: '开发完成后价值可合理预测',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  construction_cost_available: {
    label: '追加建设成本资料可采',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  sales_or_rent_forecast_reliable: {
    label: '销售或租赁预测资料可靠',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  has_land_acquisition_cost_docs: {
    label: '具备土地取得成本资料',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  has_development_cost_docs: {
    label: '具备土地开发成本资料',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_data_reliable: {
    label: '成本参数可靠',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_market_gap_risk: {
    label: '成本与市场价值脱节风险',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_in_coverage: {
    label: '处于基准地价覆盖范围',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_has_applicable_use: {
    label: '有对应基准地价用途体系',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_is_expired: {
    label: '基准地价是否可能过期',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_doc_no: {
    label: '基准地价批准/发布文号',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_doc_name: {
    label: '基准地价文件名称',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_publish_date: {
    label: '基准地价颁布实施日期',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_base_date: {
    label: '基准地价估价基准日',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_doc_authority: {
    label: '基准地价批准/发布机关',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_rule_doc_name: {
    label: '基准地价更新管理依据',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_rule_doc_no: {
    label: '基准地价更新依据文号',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  base_price_update_cycle_years_text: {
    label: '全面更新周期年限',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_disable_threshold_years_text: {
    label: '停用阈值年限',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_name: {
    label: '委托人名称',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  transfer_purpose_mode: {
    label: '出让/评估目的模式',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  transfer_purpose: {
    label: '自定义出让目的',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  project_name_suffix: {
    label: '估价项目名称后缀',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  project_name: {
    label: '估价项目名称',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  appraisal_org: {
    label: '受托估价机构',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_user: {
    label: '土地使用者',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert']
  },
  report_no: {
    label: '评估报告编号',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  technical_report_no: {
    label: '技术报告编号',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  report_date: {
    label: '报告出具日期',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_date: {
    label: '估价期日',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_work_date: {
    label: '现场勘查与工作日期范围',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_org_code: {
    label: '委托方信用代码',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_principal: {
    label: '委托方负责人',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_org_type: {
    label: '委托方机构性质',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_address: {
    label: '委托方机构地址',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_contact: {
    label: '委托方联系人',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_phone: {
    label: '委托方联系电话',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  client_postcode: {
    label: '委托方邮编',
    tab: 'p1',
    section: '第一部分：报告基础',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_location: {
    label: '估价对象位置(简称)',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  land_plot_number: {
    label: '地块编号',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  land_location_full: {
    label: '估价对象位置全称',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  county_name: {
    label: '估价所属县市简称',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  local_city: {
    label: '估价对象所属市级',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  parcel_count: {
    label: '宗地数量',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_area: {
    label: '分摊使用权面积(㎡)',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  building_area: {
    label: '建筑总面积(㎡)',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert']
  },
  land_usage: {
    label: '土地用途',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  land_usage_key: {
    label: '土地用途选项',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  land_usage_other: {
    label: '其他土地用途',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  land_usage_short: {
    label: '设定土地用途简称',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_usage_full: {
    label: '登记土地用途全称',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert']
  },
  land_usage_current_class: {
    label: '现状分类用途',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_usage_price_class: {
    label: '价格测算用途',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_use_term: {
    label: '土地使用年限',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['property_cert', 'planning_condition']
  },
  plot_ratio_mode: {
    label: '容积率类型',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  plot_ratio: {
    label: '容积率上限/固定值',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  plot_ratio_min: {
    label: '规划容积率下限',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  plot_ratio_display: {
    label: '报告展示容积率',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  set_plot_ratio_mode: {
    label: '评估设定容积率类型',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  set_plot_ratio: {
    label: '评估设定容积率上限/固定值',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  set_plot_ratio_min: {
    label: '评估设定容积率下限',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  set_plot_ratio_display: {
    label: '报告展示设定容积率',
    hidden: true,
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  building_density_min: {
    label: '规划建筑密度下限',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  building_density_max: {
    label: '规划建筑密度上限',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  greening_rate: {
    label: '规划绿地率',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  building_height_limit: {
    label: '规划建筑限高',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  right_type: {
    label: '设定土地使用权类型',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_condition_type: {
    label: '估价设定利用条件（现状/规划）',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_development_actual: {
    label: '实际土地开发程度',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_development_set: {
    label: '设定土地开发程度',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  registered_right_type: {
    label: '原登记/历史权利性质',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  assumed_right_status: {
    label: '设定土地权利状态描述',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  registered_proof_docs: {
    label: '原始权属登记的依据文书',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  entrusted_source_docs: {
    label: '委托方提供资料清单',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_boundary_desc: {
    label: '宗地四至状况',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  planning_approval_authority: {
    label: '规划条件批准机关',
    tab: 'p2',
    section: '第二部分：规划条件',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  use_cost_approx: {
    label: '采用成本逼近法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  use_market_comp: {
    label: '采用市场比较法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  use_income_cap: {
    label: '采用收益还原法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  use_benchmark_corr: {
    label: '采用基准地价系数修正法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  use_residual: {
    label: '采用剩余法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_approx_price: {
    label: '成本逼近法单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  market_comp_price: {
    label: '市场比较法单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  income_cap_price: {
    label: '收益还原法单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  benchmark_corr_price: {
    label: '基准地价系数修正单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  residual_price: {
    label: '剩余法单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  final_unit_price: {
    label: '最终评估地面单价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  final_total_price: {
    label: '最终评估土地总价',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  final_total_price_upper: {
    label: '最终土地总价大写',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  show_price_in_text: {
    label: '正文显示方法单价',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  explain_unselected_methods: {
    label: '说明未采用方法',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  is_base_price_expired: {
    label: '基准地价是否超期',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  weight_logic_type: {
    label: '确价加权逻辑',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  method_weight_percentages: {
    label: '方法权重',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  dominant_method_name: {
    label: '主导测算方法',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  adopted_methods_summary: {
    label: '已采用估价方法汇总',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  formula_display_text: {
    label: '确价公式表达',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_basis_docs_list: {
    label: '测算依据文件清单',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['base_price_report']
  },
  valuation_basis_docs_rendered: {
    label: '测算依据文件清单(渲染)',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_approx_process_intro: {
    label: '成本逼近法测算依据段落',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_approx_analysis: {
    label: '成本逼近法结构化测算数据',
    tab: 'p5',
    section: '第五部分：估价过程-成本逼近法费用测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  income_cap_analysis: {
    label: '收益还原法结构化测算数据',
    tab: 'p5',
    section: '第五部分：估价过程-收益还原法',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cost_approx_land_class_intro: {
    label: '成本逼近法征收地类说明段落',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_level_type: {
    label: '方法适用性方案',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  method_combination_type: {
    label: '确价理由方案',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  infrastructure_type: {
    label: '基础设施方案',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  weight_rationale_text: {
    label: '采用方法理由阐述',
    hidden: true,
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_method_reasons: {
    label: '估价方法选用理由段落',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_method_applicability: {
    label: '评估方法适用性阐述段落',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  final_price_determination: {
    label: '价格加权确定理由段落',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  valuation_result_statement: {
    label: '确定估价结果正文',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  infrastructure_detail: {
    label: '基础设施开发程度段落',
    tab: 'p4',
    section: '第四部分：确价测算',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  ownership_scenario_type: {
    label: '权属情形',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  asset_use_category: {
    label: '土地用途内部大类',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  asset_use_category_other: {
    label: '其他土地用途名称',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  has_other_rights_limit: {
    label: '存在他项权利限制',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  other_rights_limit_desc: {
    label: '他项权利限制具体说明',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  basis_docs_list: {
    label: '权属与规划依据文件清单',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: ['planning_condition']
  },
  basis_docs_rendered: {
    label: '依据文件清单(渲染)',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  basis_docs_phrase: {
    label: '依据文件清单话术句式',
    tab: 'p3',
    section: '第三部分：土地权属及原始证照信息',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  acquisition_land_class: {
    label: '成本逼近法征收地类',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  acquisition_land_subclass: {
    label: '成本逼近法征收地类细分类',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  acquisition_land_class_confirmed: {
    label: '成本逼近法征收地类确认状态',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  local_compensation_policy_name: {
    label: '市级/县级配套补偿政策名称',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  local_compensation_policy_no: {
    label: '市级/县级配套补偿政策文号',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  local_compensation_policy_date: {
    label: '市级/县级配套补偿政策发布日期',
    tab: 'p5',
    section: '成本逼近法政策依据与征收地类',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  acquisition_approval_doc_name: {
    label: '征地或农转用批复文件名称',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  acquisition_approval_doc_no: {
    label: '征地或农转用批复文号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  acquisition_approval_doc_date: {
    label: '征地或农转用批复日期',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  gov_approval_name: {
    label: '政府批复文件名称',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  gov_approval_no: {
    label: '政府批复文号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  gov_approval_date: {
    label: '政府批复日期',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: ['planning_condition']
  },
  original_land_owner_desc: {
    label: '原土地权属状况描述',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: []
  },
  approval_authority: {
    label: '批准机关',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: []
  },
  approval_transfer_date: {
    label: '批准农转用日期',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant'],
    attachmentTypes: []
  },
  land_usage_basis: {
    label: '土地用途依据',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  land_area_basis: {
    label: '使用权面积依据',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_doc_name: {
    label: '基准地价文件名称',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_doc_no: {
    label: '基准地价批准文号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_publish_date: {
    label: '基准地价颁布实施日期',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_base_date: {
    label: '基准地价估价基准日',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  base_price_doc_authority: {
    label: '基准地价批准机关',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  house_cert_name: {
    label: '房屋所有权证名称',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete', 'historical_unregistered'],
    attachmentTypes: ['property_cert']
  },
  house_cert_no: {
    label: '房屋所有权证编号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete', 'historical_unregistered'],
    attachmentTypes: ['property_cert']
  },
  area_docs_desc_name: {
    label: '面积依据文件名',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['historical_unregistered'],
    attachmentTypes: []
  },
  registered_house_area: {
    label: '房证登记建筑面积',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete', 'historical_unregistered'],
    attachmentTypes: ['property_cert']
  },
  proof_doc_name: {
    label: '权属证明文件名',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['historical_unregistered', 'new_grant'],
    attachmentTypes: []
  },
  proof_doc_date: {
    label: '权属证明日期',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['historical_unregistered', 'new_grant'],
    attachmentTypes: []
  },

  buy_year: {
    label: '购房年份',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['historical_unregistered'],
    attachmentTypes: []
  },
  room_detail_location: {
    label: '房间详细位置坐落',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['historical_unregistered', 'registered_complete'],
    attachmentTypes: ['property_cert']
  },
  land_cert_name: {
    label: '土地使用权证名称',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete'],
    attachmentTypes: ['property_cert']
  },
  land_cert_no: {
    label: '土地使用权证编号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete'],
    attachmentTypes: ['property_cert']
  },
  land_use_type: {
    label: '土地使用权类型描述',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['registered_complete', 'historical_unregistered'],
    attachmentTypes: []
  },
  land_use_years: {
    label: '土地使用年限',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  right_cert_no: {
    label: '权利证书号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  real_estate_cert_no: {
    label: '不动产权证书编号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  owner_name: {
    label: '权利人',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  registration_time: {
    label: '登记时间',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  cadastral_map_no: {
    label: '地籍图号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  parcel_no: {
    label: '宗地号',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  },
  memo: {
    label: '附记',
    tab: 'p3',
    section: '附件识别依据与细节字段',
    scenarios: ['new_grant', 'historical_unregistered', 'registered_complete', 'mixed_manual'],
    attachmentTypes: []
  }
};

// 渐进式多态桥接，完美向下兼容旧有 fieldToLabel 属性
const fieldToLabel = {};
Object.keys(FIELD_REGISTRY).forEach(key => {
  fieldToLabel[key] = FIELD_REGISTRY[key].label;
});

// 三大正文的响应式结构化 segments 变量定义与透视模式开关
const land_registration_desc_segments = ref([]);
const land_right_desc_segments = ref([]);
const land_use_status_desc_segments = ref([]);
const showPerspective = ref(false);
const valuation_method_reasons_segments = ref([]);
const valuation_method_applicability_segments = ref([]);
const final_price_determination_segments = ref([]);
const valuation_result_statement_segments = ref([]);
const infrastructure_detail_segments = ref([]);
const formula_display_text_segments = ref([]);
const showValuationPerspective = ref(false);

// 2. OCR 直贴控制状态
const ocrRawText = ref('');
const ocrType = ref('property_cert');
const ocrMinTextChars = ref(80);
const sitePhotoItems = ref([]);

const isSuffixUnlocked = ref(false);
const TEST_VALUATION_BASIS_DOCS_DEFAULT = [
  '《湖南省人民政府关于调整湖南省征地补偿标准的通知》（湘政发〔2024〕1号，2024年1月31日）',
  '《湖南省自然资源厅关于调整征收农用地补偿区片空间范围的通知》（湘自资发〔2024〕7号，2024年2月1日）',
  '《永州市集体土地与房屋征收补偿安置办法》（永政发〔2024〕4号，2024年5月11日）'
].join('\n');

const unlockProjectNameSuffix = () => {
  if (confirm("警告：当前后缀为标准法定词汇，非必要请勿修改。确定要修改吗？")) {
    isSuffixUnlocked.value = true;
  }
};

const onTransferPurposeModeChange = () => {
  onFieldInput('transfer_purpose_mode');
  if (form.transfer_purpose_mode.value !== '其他') {
    form.transfer_purpose.value = form.transfer_purpose_mode.value;
    onFieldInput('transfer_purpose');
  }
};

const developmentDegreeOptions = [
  { label: '三通一平（通路、通电、供水及场地平整）', value: '宗地红线外“三通”（通路、通电、供水）及红线内场地平整' },
  { label: '五通一平（通路、通电、供水、排水、通讯及场地平整）', value: '宗地红线外“五通”（通路、通电、供水、排水、通讯）及红线内场地平整' },
  { label: '七通一平（通路、通电、供水、排水、通讯、通气、通热及场地平整）', value: '宗地红线外“七通”（通路、通电、供水、排水、通讯、通气、通热）及红线内场地平整' }
];

const landUsageOptions = [
  { key: 'residential', label: '居住用地', report: '居住用地', currentClass: '居住用地', priceClass: '居住用地', category: 'residential', keywords: ['住宅', '居住', '公寓'] },
  { key: 'commercial', label: '商业服务业用地', report: '商业服务业用地', currentClass: '商业服务业用地', priceClass: '商业服务业用地', category: 'commercial', keywords: ['商业', '商服', '商务', '零售', '餐饮', '旅馆', '娱乐', '金融'] },
  { key: 'industrial', label: '工矿用地', report: '工矿用地', currentClass: '工矿用地', priceClass: '工矿用地', category: 'industrial', keywords: ['工业', '工矿', '厂房', '制造'] },
  { key: 'warehouse', label: '仓储用地', report: '仓储用地', currentClass: '仓储用地', priceClass: '仓储用地', category: 'industrial', keywords: ['仓储', '物流', '仓库'] },
  { key: 'public', label: '公共管理与公共服务用地', report: '公共管理与公共服务用地', currentClass: '公共管理与公共服务用地', priceClass: '公共管理与公共服务用地', category: 'public', keywords: ['公共', '机关', '教育', '医疗', '文化', '体育', '科研', '卫生'] },
  { key: 'transportation', label: '交通运输用地', report: '交通运输用地', currentClass: '交通运输用地', priceClass: '交通运输用地', category: 'public', keywords: ['交通', '道路', '铁路', '港口', '机场'] },
  { key: 'utility', label: '公用设施用地', report: '公用设施用地', currentClass: '公用设施用地', priceClass: '公用设施用地', category: 'public', keywords: ['公用', '供水', '排水', '供电', '燃气', '环卫'] },
  { key: 'green', label: '绿地与开敞空间用地', report: '绿地与开敞空间用地', currentClass: '绿地与开敞空间用地', priceClass: '绿地与开敞空间用地', category: 'public', keywords: ['绿地', '公园', '广场', '开敞'] },
  { key: 'special', label: '特殊用地', report: '特殊用地', currentClass: '特殊用地', priceClass: '特殊用地', category: 'other', keywords: ['特殊', '军事', '宗教', '殡葬'] },
  { key: 'other', label: '其他', report: '', currentClass: '', priceClass: '', category: 'other', keywords: [] }
];

const landUsageByKey = Object.fromEntries(landUsageOptions.map(item => [item.key, item]));

const developmentDegreeDetail = (value) => {
  const text = String(value || '');
  if (text.includes('七通')) return '七通：通路、通电、供水、排水、通讯、通气、通热；一平：红线内场地平整';
  if (text.includes('五通')) return '五通：通路、通电、供水、排水、通讯；一平：红线内场地平整';
  if (text.includes('三通')) return '三通：通路、通电、供水；一平：红线内场地平整';
  return '';
};

const getDevelopmentBadges = (value) => {
  const text = String(value || '');
  const hasTong = text.includes('通');
  return [
    { name: '路', active: hasTong && (text.includes('路') || text.includes('三通') || text.includes('五通') || text.includes('七通')), desc: '通路' },
    { name: '电', active: hasTong && (text.includes('电') || text.includes('三通') || text.includes('五通') || text.includes('七通')), desc: '通电' },
    { name: '水', active: hasTong && (text.includes('水') || text.includes('供水') || text.includes('给水') || text.includes('三通') || text.includes('五通') || text.includes('七通')), desc: '供水/给水' },
    { name: '排', active: hasTong && (text.includes('排') || text.includes('排水') || text.includes('五通') || text.includes('七通')), desc: '排水' },
    { name: '讯', active: hasTong && (text.includes('讯') || text.includes('通讯') || text.includes('通信') || text.includes('五通') || text.includes('七通')), desc: '通讯/通信' },
    { name: '气', active: hasTong && (text.includes('气') || text.includes('通气') || text.includes('燃气') || text.includes('七通')), desc: '通气/燃气' },
    { name: '热', active: hasTong && (text.includes('热') || text.includes('通热') || text.includes('七通')), desc: '通热/供暖' },
    { name: '平', active: text.includes('平') || text.includes('场地平整'), desc: '红线内场地平整' }
  ];
};

// 3. 核心表单响应式状态机
// value + origin + is_dirty 三维签名，完美支持主权秒级回归人工
const form = reactive({
  // 1. 📁 第一章：报告基本信息与地理区划
  client_name: { value: '通道侗族自治县自然资源局', origin: 'manual', is_dirty: false },
  transfer_purpose_mode: { value: '拟挂牌出让', origin: 'manual', is_dirty: false },
  transfer_purpose: { value: '拟挂牌出让', origin: 'manual', is_dirty: false },
  project_name_suffix: { value: '国有建设用地使用权市场价格评估', origin: 'manual', is_dirty: false },
  project_name: { value: '通道侗族自治县自然资源局办理土地使用权出让手续涉及位于通道县双江镇城南街一宗住宅用途国有土地使用权市场价格评估', origin: 'manual', is_dirty: false },
  appraisal_org: { value: '湖南兆财不动产规划评估有限公司', origin: 'manual', is_dirty: false },
  land_user: { value: '黄璞', origin: 'manual', is_dirty: false },
  report_no: { value: '（湖南）湘兆财土地[2026]（估）字第ZC0005号', origin: 'manual', is_dirty: false },
  technical_report_no: { value: '（湖南）湘兆财土地[2026]（技）字第ZC0005号', origin: 'manual', is_dirty: false },
  report_date: { value: '2026年05月08日', origin: 'manual', is_dirty: false },
  valuation_date: { value: '2026年04月23日', origin: 'manual', is_dirty: false },
  valuation_work_date: { value: '2026年4月23日至2026年4月27日', origin: 'manual', is_dirty: false },
  client_org_code: { value: '11431230MB16183635', origin: 'manual', is_dirty: false },
  client_principal: { value: '杨理雄', origin: 'manual', is_dirty: false },
  client_org_type: { value: '政府机关', origin: 'manual', is_dirty: false },
  client_address: { value: '湖南省怀化市通道侗族自治县双江镇友谊街3号', origin: 'manual', is_dirty: false },
  client_contact: { value: '袁先生', origin: 'manual', is_dirty: false },
  client_phone: { value: '13974595151', origin: 'manual', is_dirty: false },
  client_postcode: { value: '418500', origin: 'manual', is_dirty: false },

  // 2. 📐 第二章：土地利用条件与规划限制指标
  land_location: { value: '通道县双江镇城南街', origin: 'manual', is_dirty: false },
  land_plot_number: { value: '', origin: 'manual', is_dirty: false },
  land_location_full: { value: '通道县双江镇城南街', origin: 'manual', is_dirty: false },
  county_name: { value: '通道县', origin: 'manual', is_dirty: false },
  local_city: { value: '怀化市', origin: 'manual', is_dirty: false },
  parcel_count: { value: '一宗', origin: 'manual', is_dirty: false },
  land_area: { value: '25.32', origin: 'manual', is_dirty: false },
  building_area: { value: '107', origin: 'manual', is_dirty: false },
  plot_ratio_mode: { value: 'range', origin: 'manual', is_dirty: false },
  plot_ratio: { value: '4.23', origin: 'manual', is_dirty: false },
  plot_ratio_min: { value: '0.7', origin: 'manual', is_dirty: false },
  plot_ratio_display: { value: '0.7-4.23', origin: 'manual', is_dirty: false },
  set_plot_ratio_mode: { value: 'fixed', origin: 'manual', is_dirty: false },
  set_plot_ratio: { value: '', origin: 'manual', is_dirty: false },
  set_plot_ratio_min: { value: '', origin: 'manual', is_dirty: false },
  set_plot_ratio_display: { value: '', origin: 'manual', is_dirty: false },
  building_density_min: { value: '35%', origin: 'manual', is_dirty: false },
  building_density_max: { value: '55%', origin: 'manual', is_dirty: false },
  greening_rate: { value: '≤15%', origin: 'manual', is_dirty: false },
  building_height_limit: { value: '24米', origin: 'manual', is_dirty: false },
  land_use_term: { value: '70年', origin: 'manual', is_dirty: false },
  land_use_term_years: { value: '70', origin: 'manual', is_dirty: false },
  right_type: { value: '出让', origin: 'manual', is_dirty: false },
  land_usage_key: { value: 'residential', origin: 'manual', is_dirty: false },
  land_usage_other: { value: '', origin: 'manual', is_dirty: false },
  land_usage: { value: '居住用地', origin: 'generated', is_dirty: false },
  land_usage_short: { value: '居住用地', origin: 'generated', is_dirty: false },
  land_usage_full: { value: '居住用地', origin: 'generated', is_dirty: false },
  land_usage_current_class: { value: '居住用地', origin: 'generated', is_dirty: false },
  land_usage_price_class: { value: '居住用地', origin: 'generated', is_dirty: false },
  land_boundary_desc: { value: '东临建筑物，南临建筑物，西临长征南路，北临建筑物', origin: 'manual', is_dirty: false },
  planning_approval_authority: { value: '通道县自然资源局', origin: 'manual', is_dirty: false },
  
  valuation_condition_type: { value: '现状', origin: 'manual', is_dirty: false },
  land_development_actual: { value: '宗地红线外“五通”（通路、通电、供水、排水、通讯）及红线内场地平整', origin: 'manual', is_dirty: false },
  land_development_set: { value: '宗地红线外“五通”（通路、通电、供水、排水、通讯）及红线内场地平整', origin: 'manual', is_dirty: false },
  registered_right_type: { value: '行政划拨', origin: 'manual', is_dirty: false },
  assumed_right_status: { value: '无他项权利的完全权利条件', origin: 'manual', is_dirty: false },
  registered_proof_docs: { value: '《土地登记申请书》和《土地登记审批表》', origin: 'manual', is_dirty: false },
  entrusted_source_docs: { value: '《土地登记审批表》（编号：（2002）第032号）\n《土地登记申请书》（编号：他项（2002）032）\n《土地分户分摊面积明细表》', origin: 'manual', is_dirty: false },
  regional_factor_title: { value: '土地市场状况', origin: 'manual', is_dirty: false },
  other_special_notes_ref: { value: '第十一部分  其他需要说明的事项', origin: 'manual', is_dirty: false },

  // 3. ⚖️ 第四章：评估方法选择与加权确价
  comparable_case_count: { value: 3, origin: 'manual', is_dirty: false },
  case_similarity_level: { value: '高', origin: 'manual', is_dirty: false },
  case_time_valid: { value: true, origin: 'manual', is_dirty: false },
  market_activity_level: { value: '高', origin: 'manual', is_dirty: false },

  has_stable_income_data: { value: true, origin: 'manual', is_dirty: false },
  income_can_be_separated: { value: true, origin: 'manual', is_dirty: false },
  rent_market_activity_level: { value: '高', origin: 'manual', is_dirty: false },
  cap_rate_source_available: { value: true, origin: 'manual', is_dirty: false },

  has_development_plan: { value: true, origin: 'manual', is_dirty: false },
  development_value_measurable: { value: true, origin: 'manual', is_dirty: false },
  construction_cost_available: { value: true, origin: 'manual', is_dirty: false },
  sales_or_rent_forecast_reliable: { value: true, origin: 'manual', is_dirty: false },

  has_land_acquisition_cost_docs: { value: true, origin: 'manual', is_dirty: false },
  has_development_cost_docs: { value: true, origin: 'manual', is_dirty: false },
  cost_data_reliable: { value: true, origin: 'manual', is_dirty: false },
  cost_market_gap_risk: { value: '低', origin: 'manual', is_dirty: false },

  base_price_in_coverage: { value: true, origin: 'manual', is_dirty: false },
  base_price_has_applicable_use: { value: true, origin: 'manual', is_dirty: false },
  base_price_is_expired: { value: false, origin: 'generated', is_dirty: false },
  base_price_doc_no: { value: '', origin: 'manual', is_dirty: false },
  base_price_doc_name: { value: '', origin: 'manual', is_dirty: false },
  base_price_publish_date: { value: '', origin: 'manual', is_dirty: false },
  base_price_base_date: { value: '', origin: 'manual', is_dirty: false },
  base_price_doc_authority: { value: '', origin: 'manual', is_dirty: false },
  base_price_rule_doc_name: { value: '《关于进一步做好湖南省公示地价体系建设和管理有关工作的通知》', origin: 'manual', is_dirty: false },
  base_price_rule_doc_no: { value: '湘自资办发[2022]23号', origin: 'manual', is_dirty: false },
  base_price_update_cycle_years_text: { value: '三', origin: 'manual', is_dirty: false },
  base_price_disable_threshold_years_text: { value: '六', origin: 'manual', is_dirty: false },

  use_cost_approx: { value: true, origin: 'manual', is_dirty: false },
  use_market_comp: { value: true, origin: 'manual', is_dirty: false },
  use_income_cap: { value: false, origin: 'manual', is_dirty: false },
  use_benchmark_corr: { value: false, origin: 'manual', is_dirty: false },
  use_residual: { value: false, origin: 'manual', is_dirty: false },
  
  cost_approx_price: { value: '189.9', origin: 'manual', is_dirty: false },
  market_comp_price: { value: '', origin: 'generated', is_dirty: false },
  income_cap_price: { value: '1329.5', origin: 'manual', is_dirty: false },
  benchmark_corr_price: { value: '895.7', origin: 'manual', is_dirty: false },
  residual_price: { value: '2510.5', origin: 'manual', is_dirty: false },
  market_comp_analysis: { value: null, origin: 'generated', is_dirty: false },
  market_comp_evidence_snapshot_ids: { value: [], origin: 'generated', is_dirty: false },
  market_comp_location_snapshot_ids: { value: [], origin: 'generated', is_dirty: false },
  market_comp_site_snapshot_ids: { value: [], origin: 'generated', is_dirty: false },
  market_comp_step1_instances: { value: '', origin: 'generated', is_dirty: false },
  market_comp_basic_rows: { value: [], origin: 'generated', is_dirty: false },
  market_comp_factor_condition_rows: { value: [], origin: 'generated', is_dirty: false },
  market_comp_time_index_rows: { value: [], origin: 'generated', is_dirty: false },
  market_comp_factor_index_rows: { value: [], origin: 'generated', is_dirty: false },
  market_comp_correction_rows: { value: [], origin: 'generated', is_dirty: false },
  market_comp_step4_solve: { value: '', origin: 'generated', is_dirty: false },
  market_comp_comparable_basis: { value: '', origin: 'generated', is_dirty: false },
  market_comp_factor_selection: { value: '', origin: 'generated', is_dirty: false },
  market_comp_condition_intro: { value: '', origin: 'generated', is_dirty: false },
  market_comp_index_basis: { value: '', origin: 'generated', is_dirty: false },
  market_comp_verification: { value: '', origin: 'generated', is_dirty: false },
  cost_approx_analysis: { value: null, origin: 'generated', is_dirty: false },
  income_cap_analysis: { value: null, origin: 'generated', is_dirty: false },
  benchmark_corr_analysis: { value: null, origin: 'generated', is_dirty: false },
  residual_analysis: { value: null, origin: 'generated', is_dirty: false },
  final_unit_price: { value: '', origin: 'manual', is_dirty: false },
  final_total_price: { value: '', origin: 'manual', is_dirty: false },
  final_total_price_upper: { value: '', origin: 'manual', is_dirty: false },
  requires_manual_final_price: { value: false, origin: 'generated', is_dirty: false },
  show_price_in_text: { value: true, origin: 'generated', is_dirty: false },
  explain_unselected_methods: { value: true, origin: 'generated', is_dirty: false },
  is_base_price_expired: { value: false, origin: 'generated', is_dirty: false },

  weight_logic_type: { value: 'weighted_average', origin: 'manual', is_dirty: false },
  method_weight_percentages: { value: { use_cost_approx: '50', use_market_comp: '50' }, origin: 'manual', is_dirty: false },
  dominant_method_name: { value: '剩余法', origin: 'manual', is_dirty: false },
  formula_display_text: { value: '成本逼近法×50%+市场比较法×50%', origin: 'generated', is_dirty: false },
  land_level_type: { value: 'residential_level_3', origin: 'manual', is_dirty: false },
  method_combination_type: { value: 'residential_residual_only', origin: 'manual', is_dirty: false },
  infrastructure_type: { value: 'five_通_residential', origin: 'manual', is_dirty: false },
  weight_rationale_text: { value: '', origin: 'generated', is_dirty: false },
  valuation_basis_docs_list: { value: TEST_VALUATION_BASIS_DOCS_DEFAULT, origin: 'manual', is_dirty: false },
  valuation_basis_docs_rendered: { value: '', origin: 'generated', is_dirty: false },
  
  valuation_method_reasons: { value: '本次评估采用成本逼近法和市场比较法。成本逼近法可反映土地取得及开发投入水平；市场比较法可通过类似案例比较修正测算土地价格。', origin: 'generated', is_dirty: false },
  valuation_method_applicability: { value: '估价对象为已开发建设土地，基础设施达到红线外五通及红线内场地平整，因此适用成本逼近法。由于同类住宅用地交易实例较多，也适用市场比较法。', origin: 'generated', is_dirty: false },
  final_price_determination: { value: '', origin: 'generated', is_dirty: false },
  valuation_result_statement: { value: '', origin: 'generated', is_dirty: false },
  infrastructure_detail: { value: '宗地红线外“五通”（即通路、通电、供水、排水、通讯），宗地红线内场地平整。', origin: 'generated', is_dirty: false },
  cost_approx_land_class_intro: { value: '', origin: 'generated', is_dirty: false },
  cost_approx_process_intro: { value: '', origin: 'generated', is_dirty: false },

  // 4. 📜 第三章：土地权属及证照信息（智能草稿 + 最终正文）
  ownership_scenario_type: { value: 'historical_unregistered', origin: 'manual', is_dirty: false },
  land_status_type: { value: 'historical_unregistered', origin: 'manual', is_dirty: false },
  asset_use_category: { value: 'residential', origin: 'generated', is_dirty: false },
  asset_use_category_other: { value: '', origin: 'generated', is_dirty: false },
  has_other_rights_limit: { value: false, origin: 'manual', is_dirty: false },
  other_rights_limit_desc: { value: '', origin: 'manual', is_dirty: false },
  land_registration_desc: { value: '', origin: 'generated', is_dirty: false },
  land_right_desc: { value: '', origin: 'generated', is_dirty: false },
  land_use_status_desc: { value: '', origin: 'generated', is_dirty: false },
  basis_docs_list: { value: '', origin: 'manual', is_dirty: false },
  basis_docs_rendered: { value: '', origin: 'generated', is_dirty: false },
  basis_docs_phrase: { value: '', origin: 'generated', is_dirty: false },

  acquisition_land_class: { value: '耕地', origin: 'manual', is_dirty: false },
  acquisition_land_subclass: { value: '水田', origin: 'manual', is_dirty: false },
  acquisition_land_class_confirmed: { value: true, origin: 'manual', is_dirty: false },
  local_compensation_policy_name: { value: '', origin: 'generated', is_dirty: false },
  local_compensation_policy_no: { value: '', origin: 'generated', is_dirty: false },
  local_compensation_policy_date: { value: '', origin: 'generated', is_dirty: false },
  acquisition_approval_doc_name: { value: '关于通道县2002年第七批次建设用地农用地转用和土地征收的批复', origin: 'manual', is_dirty: false },
  acquisition_approval_doc_no: { value: '湘政地〔2002〕1205号', origin: 'manual', is_dirty: false },
  acquisition_approval_doc_date: { value: '2002年9月5日', origin: 'manual', is_dirty: false },
  gov_approval_name: { value: '关于通道县2002年第七批次建设用地农用地转用和土地征收的批复', origin: 'manual', is_dirty: false },
  gov_approval_no: { value: '湘政地〔2002〕1205号', origin: 'manual', is_dirty: false },
  gov_approval_date: { value: '2002年9月5日', origin: 'manual', is_dirty: false },
  original_land_owner_desc: { value: '', origin: 'manual', is_dirty: false },
  approval_authority: { value: '通道县人民政府', origin: 'manual', is_dirty: false },
  approval_transfer_date: { value: '2002年12月30日', origin: 'manual', is_dirty: false },
  land_usage_basis: { value: '', origin: 'manual', is_dirty: false },
  land_area_basis: { value: '', origin: 'manual', is_dirty: false },
  base_price_doc_name: { value: '', origin: 'manual', is_dirty: false },
  base_price_doc_no: { value: '', origin: 'manual', is_dirty: false },
  base_price_publish_date: { value: '', origin: 'manual', is_dirty: false },
  base_price_base_date: { value: '', origin: 'manual', is_dirty: false },
  base_price_doc_authority: { value: '', origin: 'manual', is_dirty: false },
  
  house_cert_name: { value: '房屋所有权证', origin: 'manual', is_dirty: false },
  house_cert_no: { value: '通房字第5172号', origin: 'manual', is_dirty: false },
  area_docs_desc_name: { value: '土地资产评估委托书、土地分户分摊面积明细表', origin: 'manual', is_dirty: false },
  registered_house_area: { value: '107.13', origin: 'manual', is_dirty: false },
  proof_doc_name: { value: '通道县房屋登记核发权证申请表', origin: 'manual', is_dirty: false },
  proof_doc_date: { value: '2002年12月30日', origin: 'manual', is_dirty: false },

  buy_year: { value: '2002年', origin: 'manual', is_dirty: false },
  room_detail_location: { value: '通道侗族自治县双江镇城南街皮革厂家属楼3栋4层404房', origin: 'manual', is_dirty: false },
  
  land_cert_name: { value: '', origin: 'manual', is_dirty: false },
  land_cert_no: { value: '', origin: 'manual', is_dirty: false },
  land_use_type: { value: '', origin: 'manual', is_dirty: false },
  right_cert_no: { value: '通房字第5172号', origin: 'manual', is_dirty: false },
  real_estate_cert_no: { value: '湘(2021)通道县不动产权第0001234号', origin: 'manual', is_dirty: false },
  owner_name: { value: '通道县公路管理站', origin: 'manual', is_dirty: false },
  registration_time: { value: '2002年9月28日', origin: 'manual', is_dirty: false },
  cadastral_map_no: { value: '001', origin: 'manual', is_dirty: false },
  parcel_no: { value: '12-34-56', origin: 'manual', is_dirty: false },
  memo: { value: '无他项权利限制', origin: 'manual', is_dirty: false }
});

// 💡 V6.7.0 一主多从 PC 桌面端级智醒全案用途方案联动机制
watch(
  () => [form.land_usage_key.value, form.land_usage_other.value],
  () => {
    syncLandUsageFields();
    const category = form.asset_use_category.value || 'other';
    const conditionType = category === 'residential' ? '现状' : '规划';
    if (form.valuation_condition_type.value !== conditionType) {
      form.valuation_condition_type.value = conditionType;
    }
    regenerateOwnershipDraft(false);
    regenerateValuationNarratives(false);
  }
);

const generatedBackfillKeys = new Set([
  'land_registration_desc',
  'land_right_desc',
  'land_use_status_desc',
  'basis_docs_rendered',
  'basis_docs_phrase',
  'formula_display_text',
  'valuation_basis_docs_rendered',
  'valuation_method_reasons',
  'valuation_method_applicability',
  'final_price_determination',
  'valuation_result_statement',
  'infrastructure_detail',
  'cost_approx_land_class_intro',
  'cost_approx_process_intro'
]);

// 💡 V6.2 细节折叠面板，动态计算场景推荐关注高亮置顶字段与其它要素
const detailFieldKeys = [
  'acquisition_approval_doc_name', 'acquisition_approval_doc_no', 'acquisition_approval_doc_date',
  'gov_approval_name', 'gov_approval_no', 'gov_approval_date', 'original_land_owner_desc', 'approval_authority',
  'approval_transfer_date', 'land_usage_basis', 'land_area_basis',
  'base_price_doc_name', 'base_price_doc_no', 'base_price_publish_date', 'base_price_base_date', 'base_price_doc_authority',
  'house_cert_name', 'house_cert_no',
  'area_docs_desc_name', 'registered_house_area', 'proof_doc_name', 'proof_doc_date',
  'buy_year', 'room_detail_location',
  'land_cert_name', 'land_cert_no', 'land_use_type',
  'right_cert_no', 'real_estate_cert_no', 'owner_name',
  'registration_time', 'cadastral_map_no', 'parcel_no', 'memo'
];

const basisDocsOptions = computed(() => {
  const raw = form.basis_docs_list.value || '';
  return raw.split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .map(line => {
      const match = line.match(/《([^》]+)》/);
      return match ? `《${match[1]}》` : (line.startsWith('《') ? line : `《${line}》`);
    });
});

const sharedBasisReferenceOptions = computed(() => {
  const values = [];
  const appendLines = (raw) => String(raw || '').split(/\n+/).map(item => item.trim()).filter(Boolean).forEach(item => values.push(item));
  appendLines(form.basis_docs_list?.value);
  appendLines(form.valuation_basis_docs_list?.value);
  (costAnalysis.value?.policy_documents || []).forEach(item => {
    if (item?.name) values.push(item.document_no ? `${item.name}（${item.document_no}）` : item.name);
    if (item?.reference_text) values.push(item.reference_text);
  });
  (uploadedAttachments.value || []).forEach(item => values.push(item.cleanedName || item.fileName || item.name || ''));
  return [...new Set(values.map(item => String(item || '').trim()).filter(Boolean))];
});

const applyBasisReference = (target, value, mode = 'replace') => {
  const selected = String(value || '').trim();
  if (!target || !selected) return;
  const current = String(target.value ?? target ?? '').trim();
  const next = mode === 'append' && current && !current.includes(selected) ? `${current}；${selected}` : selected;
  if (typeof target === 'object' && Object.prototype.hasOwnProperty.call(target, 'value')) target.value = next;
};

const addSharedValuationBasis = (value) => {
  const selected = String(value || '').trim();
  if (!selected) return;
  const lines = String(form.valuation_basis_docs_list?.value || '').split(/\n+/).map(item => item.trim()).filter(Boolean);
  if (!lines.includes(selected)) lines.push(selected);
  form.valuation_basis_docs_list.value = lines.join('\n');
  form.valuation_basis_docs_list.origin = 'manual';
  form.valuation_basis_docs_list.is_dirty = true;
  showToast('已加入共享测算依据清单', 'success');
};

const recommendedFields = computed(() => {
  const scenario = form.ownership_scenario_type.value;
  const category = form.asset_use_category.value;
  const isIndustrialOrPublic = category === 'industrial' || category === 'public';
  
  const houseRelatedKeys = new Set([
    'house_cert_name', 'house_cert_no', 'registered_house_area', 
    'buy_year', 'room_detail_location', 
    'area_docs_desc_name'
  ]);

  return detailFieldKeys.filter(key => {
    if (isIndustrialOrPublic && houseRelatedKeys.has(key)) {
      return false;
    }
    const reg = FIELD_REGISTRY[key];
    return reg && !reg.hidden && reg.scenarios.includes(scenario);
  });
});

const otherFields = computed(() => {
  const recs = new Set(recommendedFields.value);
  const category = form.asset_use_category.value;
  const isIndustrialOrPublic = category === 'industrial' || category === 'public';
  
  const houseRelatedKeys = new Set([
    'house_cert_name', 'house_cert_no', 'registered_house_area', 
    'buy_year', 'room_detail_location', 
    'area_docs_desc_name'
  ]);

  return detailFieldKeys.filter(key => {
    if (isIndustrialOrPublic && houseRelatedKeys.has(key)) {
      return false;
    }
    const reg = FIELD_REGISTRY[key];
    return reg && !reg.hidden && reg.scenarios.includes(form.ownership_scenario_type.value) && !recs.has(key);
  });
});

const valuationMethodOptions = [
  { flag: 'use_cost_approx', name: '成本逼近法', price: 'cost_approx_price' },
  { flag: 'use_market_comp', name: '市场比较法', price: 'market_comp_price' },
  { flag: 'use_income_cap', name: '收益还原法', price: 'income_cap_price' },
  { flag: 'use_benchmark_corr', name: '基准地价系数修正法', price: 'benchmark_corr_price' },
  { flag: 'use_residual', name: '剩余法', price: 'residual_price' }
];

const selectedValuationMethods = computed(() => {
  return valuationMethodOptions
    .filter(item => Boolean(form[item.flag]?.value))
    .map(item => ({
      ...item,
      priceValue: String(form[item.price]?.value || '').trim()
    }));
});

const ensureMethodWeights = () => {
  const selected = selectedValuationMethods.value;
  if (!form.method_weight_percentages.value || typeof form.method_weight_percentages.value !== 'object') {
    form.method_weight_percentages.value = {};
  }
  if (!selected.length) return;
  const existing = form.method_weight_percentages.value;
  const activeFlags = new Set(selected.map(item => item.flag));
  Object.keys(existing).forEach(flag => {
    if (!activeFlags.has(flag)) delete existing[flag];
  });
  const missing = selected.filter(item => existing[item.flag] === undefined || existing[item.flag] === '');
  if (missing.length || selected.some(item => existing[item.flag] === undefined)) {
    const equal = (100 / selected.length).toFixed(2).replace(/\.00$/, '');
    selected.forEach(item => {
      existing[item.flag] = equal;
    });
  }
};

const onMethodWeightInput = () => {
  form.method_weight_percentages.is_dirty = true;
  form.method_weight_percentages.origin = 'manual';
  onFieldInput('method_weight_percentages');
};

const onWeightLogicChange = () => {
  onFieldInput('weight_logic_type');
  form.requires_manual_final_price.value = false;
  form.requires_manual_final_price.origin = 'generated';
  form.requires_manual_final_price.is_dirty = false;
  ['final_unit_price', 'final_total_price', 'final_total_price_upper'].forEach(key => {
    if (form[key]) {
      form[key].value = '';
      form[key].origin = 'generated';
      form[key].is_dirty = false;
    }
  });
  ensureMethodWeights();
  regenerateValuationNarratives(false);
};

const buildFormulaText = (methods) => {
  if (!methods.length) return '';
  if (form.weight_logic_type.value === 'median') {
    return `${methods.map(item => item.name).join('、')}测算结果的中位数`;
  }
  if (form.weight_logic_type.value === 'mode') {
    return `${methods.map(item => item.name).join('、')}测算结果的众数`;
  }
  if (methods.length === 1) return methods[0].name;
  const fallback = (100 / methods.length).toFixed(2).replace(/\.00$/, '');
  return methods.map(item => `${item.name}×${form.method_weight_percentages.value[item.flag] || fallback}%`).join('+');
};

const valuationDraftPreview = computed(() => {
  const methods = selectedValuationMethods.value;
  const methodNames = methods.map(item => item.name).join('、') || '未选择评估方法';
  const formula = buildFormulaText(methods);
  const priceParts = methods
    .filter(item => item.priceValue)
    .map(item => `${item.name}单价${item.priceValue}元/平方米`);
  const priceText = priceParts.length ? `其中，${priceParts.join('，')}。` : '';
  const reasons = methods.length
    ? `本次评估采用${methodNames}。未采用方法将在正文中按资料条件另行说明。`
    : '请先勾选至少一种评估方法。';
  const applicability = methods.length
    ? `本次估价结合估价对象用途、开发程度、资料完备性及当地土地市场情况，选用${methodNames}进行测算。`
    : '请先勾选至少一种评估方法。';
  const determination = methods.length
    ? `本次综合采用${methodNames}的测算结果，按“${formula || form.formula_display_text.value}”进行分析确定最终估价结果。${priceText}`.trim()
    : '尚未形成确价理由。';
  const infrastructure = `估价对象实际土地开发程度为${form.land_development_actual.value || '待确认'}；本次设定土地开发程度为${form.land_development_set.value || '待确认'}。`;
  return {
    methods: methodNames,
    formula,
    reasons,
    applicability,
    determination,
    infrastructure
  };
});

// 监听要素，自动更新 project_name
watch(
  () => [
    form.client_name.value, 
    form.transfer_purpose.value, 
    form.land_location.value, 
    form.land_plot_number.value,
    form.parcel_count.value,
    form.land_usage.value,
    form.project_name_suffix.value
  ],
  ([client, transfer, location, plot, parcel, usage, suffix]) => {
    const fullLocation = `${location || ''}${plot || ''}`;
    form.land_location_full.value = fullLocation;
    form.land_location_full.origin = 'manual';
    nextTick(() => scheduleCostZoneRematch());

    form.project_name.value = `${client || ''}${transfer || ''}涉及位于${fullLocation}的${parcel || '一宗'}${usage || ''}${suffix || ''}`;
    form.project_name.origin = 'manual';
  },
  { immediate: true }
);

onMounted(() => {
  isLightTheme.value = localStorage.getItem('theme') === 'light';
  document.documentElement.classList.toggle('light-theme', isLightTheme.value);
  syncLegacyLandUsageFields();
  syncBasePriceExpiryFields();
  ensureMethodWeights();
  regenerateOwnershipDraft(false);
  regenerateValuationNarratives(false);
});

// Toast 控制系统
const toasts = ref([]);
let toastId = 0;
const showToast = (text, type = 'success') => {
  const id = toastId++;
  toasts.value.push({ id, text, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, 4000);
};

const normalizeNetworkError = (error, url = '') => {
  const raw = String(error?.message || error || '').trim();
  if (/network error|failed to fetch|load failed/i.test(raw)) {
    if (String(url).includes('/api/comparable-library/')) {
      return '本系统已发起请求，但网络层没有拿到响应。若当前是本机直连，通常是土地市场网拦截了本机出口；请启用云服务器爬取并确认云服务器转发脚本正在运行。';
    }
    return '本地后台服务没有响应，请确认评估报告工具后台仍在运行后刷新页面。';
  }
  return raw || '接口请求失败';
};

const apiJson = async (url, options = {}) => {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new Error(normalizeNetworkError(error, url));
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || '接口请求失败');
  return payload.data;
};

const fileTimestamp = () => {
  const now = new Date();
  const pad = value => String(value).padStart(2, '0');
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
};

const safeDownloadName = (name) => String(name || 'download').replace(/[\\/:*?"<>|]/g, '_');

const downloadBlobFile = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = safeDownloadName(filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const isoDateFromParts = (parts) => {
  if (!parts) return '';
  return `${parts.year}-${String(parts.month).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`;
};

const comparableDefaultRange = () => {
  const parts = parseCnDate(form.valuation_date.value);
  if (!parts) return { start: '', end: '' };
  return {
    start: `${parts.year - 3}-${String(parts.month).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`,
    end: isoDateFromParts(parts)
  };
};

const initializeComparableLibrary = async () => {
  const range = comparableDefaultRange();
  crawlFilters.start_date ||= range.start;
  crawlFilters.end_date ||= range.end;
  crawlFilters.xzq_dm ||= inferComparableXzqDm(form.county_name.value);
  if (isRegionNameLocationFilter(crawlFilters.location, crawlFilters.xzq_dm)) {
    crawlFilters.location = '';
  }
  crawlFilters.land_usage_key ||= form.land_usage_key.value;
  libraryFilters.start_date ||= range.start;
  libraryFilters.end_date ||= range.end;
  libraryFilters.xzq_dm ||= inferComparableXzqDm(form.county_name.value);
  libraryFilters.location = '';
  libraryFilters.land_usage_key ||= form.land_usage_key.value;
  schemeUsageKey.value = form.land_usage_key.value || 'other';
  await loadComparableRegionOptions();
  await loadCloudProxyConfig();
  await loadLandChinaAccessStatus();
  if (!comparableCases.value.length) await loadComparableCases();
};

const onComparableViewChange = async (view) => {
  if (view === 'crawl') {
    await loadCloudProxyConfig();
    await loadLandChinaAccessStatus();
  }
  if (view === 'library') {
    await loadComparableRegionOptions();
    await loadComparableCases();
  }
  if (view === 'schemes') await loadFactorScheme();
};

const loadComparableRegionOptions = async () => {
  try {
    const regions = await apiJson('/api/comparable-library/case-regions');
    comparableRegionOptions.value = mergeComparableRegionOptions(regions || []);
  } catch (error) {
    comparableRegionOptions.value = mergeComparableRegionOptions();
    showToast(`读取行政区下拉失败：${error.message}`, 'warning');
  }
};

const loadComparableCases = async () => {
  try {
    const params = new URLSearchParams({ page: '1', page_size: '100' });
    Object.entries(libraryFilters).forEach(([key, value]) => {
      if (String(value || '').trim()) params.set(key, String(value).trim());
    });
    const data = await apiJson(`/api/comparable-library/cases?${params.toString()}`);
    comparableCases.value = data.items || [];
    comparableTotal.value = data.total || 0;
  } catch (error) {
    showToast(`实例库查询失败：${error.message}`, 'error');
  }
};

const exportComparableCases = async () => {
  try {
    const params = new URLSearchParams();
    Object.entries(libraryFilters).forEach(([key, value]) => {
      if (String(value || '').trim()) params.set(key, String(value).trim());
    });
    const response = await fetch(`/api/comparable-library/cases/export?${params.toString()}`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || '实例库导出失败');
    }
    const blob = await response.blob();
    downloadBlobFile(blob, `比较实例库_${fileTimestamp()}.csv`);
      showToast('实例库当前筛选结果已导出。');
  } catch (error) {
    showToast(`实例库导出失败：${error.message}`, 'error');
  }
};

const pollComparableCrawl = async (jobId) => {
  try {
    crawlJob.value = await apiJson(`/api/comparable-library/crawl-jobs/${jobId}`);
    if (['queued', 'running'].includes(crawlJob.value.status)) {
      crawlPollTimer = window.setTimeout(() => pollComparableCrawl(jobId), 900);
    } else if (crawlJob.value.status === 'completed') {
      showToast(`抓取完成：入库${crawlJob.value.saved || 0} 宗，详情完整 ${crawlJob.value.complete || 0} 宗，待补全${crawlJob.value.partial || 0} 宗。`);
      await loadComparableCases();
    } else if (crawlJob.value.status === 'failed') {
        showToast(`抓取失败：${crawlJob.value.errors?.[0] || '未知错误'}`, 'error');
    }
    if (!['queued', 'running'].includes(crawlJob.value.status)) await loadLandChinaAccessStatus();
  } catch (error) {
    showToast(`读取抓取进度失败：${error.message}`, 'error');
  }
};

const loadLandChinaAccessStatus = async () => {
  try {
    landChinaAccessStatus.value = await apiJson('/api/comparable-library/access-status');
    if (landChinaAccessStatus.value?.proxy_config) {
      syncCloudProxyForm(landChinaAccessStatus.value.proxy_config);
    }
    return landChinaAccessStatus.value;
  } catch (error) {
    console.error('读取土地市场网访问状态失败', error);
    throw error;
  }
};

const syncCloudProxyForm = (config) => {
  cloudProxyConfig.value = config;
  cloudProxyForm.enabled = Boolean(config?.enabled);
  cloudProxyForm.proxy_url = config?.proxy_url || '';
  cloudProxyForm.proxy_token = '';
};

const loadCloudProxyConfig = async () => {
  try {
    const config = await apiJson('/api/comparable-library/proxy-config');
    syncCloudProxyForm(config);
    return config;
  } catch (error) {
    showToast(`读取云服务器配置失败：{error.message}`, 'error');
    return null;
  }
};

const saveCloudProxyConfig = async (options = {}) => {
  try {
    const payload = {
      enabled: Boolean(cloudProxyForm.enabled),
      proxy_url: String(cloudProxyForm.proxy_url || '').trim()
    };
    if (String(cloudProxyForm.proxy_token || '').trim()) {
      payload.proxy_token = String(cloudProxyForm.proxy_token).trim();
    }
    if (options.clearToken) {
      payload.clear_token = true;
    }
    const config = await apiJson('/api/comparable-library/proxy-config', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    syncCloudProxyForm(config);
    await loadLandChinaAccessStatus();
      if (!options.silent) showToast('云服务器爬取配置已保存。');
    return config;
  } catch (error) {
    showToast(`保存云服务器配置失败：{error.message}`, 'error');
    return null;
  }
};

const clearCloudProxyToken = async () => {
  await saveCloudProxyConfig({ clearToken: true });
};

const toggleCloudProxyEnabled = async () => {
  const enabled = Boolean(cloudProxyForm.enabled);
  try {
    const config = await apiJson('/api/comparable-library/proxy-config', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    syncCloudProxyForm(config);
    await loadLandChinaAccessStatus();
      showToast(enabled ? '已切换为云服务器中转。' : '已切换为本机直连，并清除旧通道冷却。');
  } catch (error) {
    cloudProxyForm.enabled = Boolean(cloudProxyConfig.value?.enabled);
    showToast(`切换访问通道失败：{error.message}`, 'error');
  }
};

const testCloudProxyConfig = async () => {
  const config = await saveCloudProxyConfig({ silent: true });
  if (!config) return;
  try {
    const result = await apiJson('/api/comparable-library/proxy-config/test', { method: 'POST' });
    syncCloudProxyForm(result.config);
    await loadLandChinaAccessStatus();
      showToast(result.message || (result.ok ? '云服务器连接正常。' : '云服务器连接失败。'), result.ok ? 'success' : 'error');
  } catch (error) {
      showToast(`测试云服务器连接失败：${error.message}`, 'error');
  }
};

const landChinaAccessText = (status) => {
  const minutes = Math.max(Math.ceil((status?.remaining_seconds || 0) / 60), 1);
  const retryAt = String(status?.blocked_until || '').replace('T', ' ');
  return `${status?.last_reason || '官网暂时拒绝 API 访问'}；约 ${minutes} 分钟后可重试${retryAt ? `（${retryAt}）` : ''}。`;
};

const landChinaAccessReadyText = (status) => {
  const last = status?.last_reason ? `上次记录：${status.last_reason}` : '未记录官网访问限制。';
  if (!status?.proxy_enabled) {
    return `当前为本机直连，系统未处于内部冷却。若土地市场网页面或抓取仍显示 Network Error，一般是官网 WAF 拦截了本机出口，建议启用云服务器爬取。${last}`;
  }
  return `当前未处于冷却，可发起抓取。{last}`;
};

const landChinaAccessChannelText = (status) => {
  if (status?.proxy_enabled) {
    return `云服务器中转${status.proxy_url ? `（${status.proxy_url}）` : ''}`;
  }
  return '本机直连';
};

const checkLandChinaAccessStatus = async () => {
  try {
    const status = await loadLandChinaAccessStatus();
    showToast(status?.blocked ? landChinaAccessText(status) : landChinaAccessReadyText(status), status?.blocked ? 'warning' : 'success');
  } catch (error) {
    showToast(`读取访问状态失败：${error.message}`, 'error');
  }
};

const normalizedComparableCrawlFilters = () => {
  const payload = { ...crawlFilters };
  payload.xzq_dm = String(payload.xzq_dm || '').trim() || inferComparableXzqDm(form.county_name.value);
  payload.location = String(payload.location || '').trim();
  if (isRegionNameLocationFilter(payload.location, payload.xzq_dm)) {
    payload.location = '';
  }
  return payload;
};

const crawlPhaseLabel = (job) => {
  if (job?.status === 'failed') return '抓取失败';
  if (job?.status === 'cancelled') return '已取消';
  if (job?.status === 'completed') return '抓取完成';
  return {
    queued: '等待开始',
    listing: '读取结果列表',
    saving_list: '保存列表记录',
    enriching_details: '补全详情'
  }[job?.phase] || '抓取中';
};

const startComparableCrawl = async () => {
  try {
    await loadLandChinaAccessStatus();
    if (landChinaAccessStatus.value?.blocked) {
      showToast(landChinaAccessText(landChinaAccessStatus.value), 'warning');
      return;
    }
    if (crawlPollTimer) window.clearTimeout(crawlPollTimer);
    const response = await fetch('/api/comparable-library/crawl-jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(normalizedComparableCrawlFilters())
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || '创建抓取任务失败');
    crawlJob.value = payload.data;
    pollComparableCrawl(payload.job_id);
  } catch (error) {
    showToast(`创建抓取任务失败：{error.message}`, 'error');
  }
};

const cancelComparableCrawl = async () => {
  if (!crawlJob.value?.job_id) return;
  try {
    crawlJob.value = await apiJson(`/api/comparable-library/crawl-jobs/${crawlJob.value.job_id}/cancel`, { method: 'POST' });
  } catch (error) {
    showToast(`取消抓取失败：{error.message}`, 'error');
  }
};

const selectedComparableCase = (slot) => selectedComparableRecords[slot];

const landChinaSupplyDetailBaseUrl = 'https://www.landchina.com/#/landSupplyDetail';

const landChinaSupplyDetailUrl = (item) => {
  const sourceUrl = String(item?.source_url || '').trim();
  if (sourceUrl.includes('/#/landSupplyDetail')) return sourceUrl;
  const gdGuid = String(item?.gd_guid || item?.id || '').trim();
  if (!gdGuid) return '';
  return `${landChinaSupplyDetailBaseUrl}?id=${encodeURIComponent(gdGuid)}&type=${encodeURIComponent('供地结果')}&path=0`;
};

const openLandChinaSupplyDetail = (item) => {
  const url = landChinaSupplyDetailUrl(item);
  if (!url) {
    showToast('该实例缺少官网 gdGuid，无法打开地块详情页。', 'warning');
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
};

const comparableEvidenceKeyword = (slot) => {
  const item = selectedComparableCase(slot);
  if (!item) return '';
  return [
    item.electronic_supervision_no,
    item.project_name,
    item.location,
  ].filter(Boolean).join(' ');
};

const copyComparableEvidenceKeyword = async (slot) => {
  const text = comparableEvidenceKeyword(slot);
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showToast(`实例 ${slot} 检索词已复制。`);
  } catch (_error) {
    showToast(`实例 ${slot} 检索词：${text}`, 'info');
  }
};

const evidenceSnapshotFor = (slot, kind) => marketEvidenceDetails[kind]?.[slot] || null;

const setEvidenceSnapshot = (slot, kind, snapshot) => {
  const config = evidenceKindConfig(kind);
  const index = comparableSlots.indexOf(slot);
  if (index < 0 || !form[config.field]) return;
  const ids = [...(form[config.field].value || [])];
  while (ids.length < comparableSlots.length) ids.push('');
  ids[index] = snapshot.snapshot_id;
  form[config.field].value = ids;
  form[config.field].origin = 'manual';
  marketEvidenceDetails[kind][slot] = snapshot;
  if (kind === 'announcement') {
    marketEvidenceSnapshots.value = comparableSlots.map(item => marketEvidenceDetails.announcement[item]).filter(Boolean);
    if (marketAnalysis.value) {
      marketAnalysis.value.evidence_snapshot_ids = ids;
      form.market_comp_analysis.value = marketAnalysis.value;
    }
  }
};

const handleComparableEvidenceUpload = async (slot, kind, event) => {
  const files = Array.from(event.target.files || []);
  event.target.value = '';
  const caseItem = selectedComparableCase(slot);
  if (!caseItem || !files.length) return;
  const imageFiles = files.filter(file => file.type.startsWith('image/'));
  if (!imageFiles.length) {
      showToast('请上传图片格式的截图。', 'warning');
    return;
  }
  const formData = new FormData();
  formData.append('case_id', caseItem.id);
  formData.append('evidence_kind', kind);
  imageFiles.forEach(file => formData.append('files', file));
  isLoading.value = true;
  loadingMessage.value = `正在保存实例 ${slot} 的${evidenceKindConfig(kind).label}...`;
  try {
    const response = await fetch('/api/comparable-library/evidence/manual', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      let message = '证据截图上传失败';
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch (_error) {}
      throw new Error(message);
    }
    const payload = await response.json();
    setEvidenceSnapshot(slot, kind, payload.data);
    if (activeTab.value === 'p5') await loadValuationProcessDraft();
    showToast(`实例 ${slot} 的${evidenceKindConfig(kind).label}已保存。`);
  } catch (error) {
    showToast(`保存证据截图失败：{error.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

const assignComparable = (slot, item) => {
  const duplicate = comparableSlots.find(key => key !== slot && selectedComparableIds[key] === item.id);
  if (duplicate) {
    showToast(`该实例已分配为实例 ${duplicate}。`, 'warning');
    return;
  }
  selectedComparableIds[slot] = item.id;
  selectedComparableRecords[slot] = item;
  marketAnalysis.value = null;
  marketEvidenceSnapshots.value = [];
  form.market_comp_analysis.value = null;
  form.market_comp_evidence_snapshot_ids.value = [];
  form.market_comp_location_snapshot_ids.value = [];
  form.market_comp_site_snapshot_ids.value = [];
  marketEvidenceKinds.forEach(kind => {
    comparableSlots.forEach(itemSlot => {
      marketEvidenceDetails[kind.key][itemSlot] = null;
    });
  });
};

const refreshCaseAdvancedJson = () => {
  const guided = new Set(caseGuidedFields.value.map(item => item.key));
  const advanced = {};
  Object.entries(caseManualForm.value || {}).forEach(([key, value]) => {
    if (!guided.has(key) && value !== null && value !== undefined && value !== '') advanced[key] = value;
  });
  caseAdvancedJson.value = JSON.stringify(advanced, null, 2);
};

const editComparableCase = async (item) => {
  editingComparableCase.value = item;
  caseDraftState.value = '';
  caseChangedKeys.value = [];
  try {
    caseFactorScheme.value = await apiJson(`/api/comparable-library/factor-schemes/${item.land_usage_key || form.land_usage_key.value || 'other'}`);
  } catch (error) {
    caseFactorScheme.value = null;
  }
  caseManualForm.value = {
    ...(item.manual_fields || {}),
    ...(item.manual_draft_fields || {})
  };
  refreshCaseAdvancedJson();
};

const closeComparableCaseEditor = () => {
  if (caseDraftSaveTimer) window.clearTimeout(caseDraftSaveTimer);
  editingComparableCase.value = null;
  caseManualForm.value = {};
  caseChangedKeys.value = [];
  caseFactorScheme.value = null;
};

const markComparableDraftChanged = (key) => {
  if (!caseChangedKeys.value.includes(key)) caseChangedKeys.value.push(key);
  scheduleComparableDraftSave();
};

const scheduleComparableDraftSave = () => {
  caseDraftState.value = '草稿待保存';
  if (caseDraftSaveTimer) window.clearTimeout(caseDraftSaveTimer);
  caseDraftSaveTimer = window.setTimeout(() => saveComparableManualDraft(true), 650);
};

const scheduleComparableAdvancedDraftSave = () => {
  try {
    const advanced = JSON.parse(caseAdvancedJson.value || '{}');
    const guided = new Set(caseGuidedFields.value.map(item => item.key));
    const previousAdvancedKeys = Object.keys(caseManualForm.value || {}).filter(key => !guided.has(key));
    new Set([...previousAdvancedKeys, ...Object.keys(advanced)]).forEach(key => {
      if (!caseChangedKeys.value.includes(key)) caseChangedKeys.value.push(key);
      caseManualForm.value[key] = Object.prototype.hasOwnProperty.call(advanced, key) ? advanced[key] : '';
    });
    scheduleComparableDraftSave();
  } catch (error) {
    caseDraftState.value = '高级字段 JSON 格式待修正';
  }
};

const buildComparableDraftPayload = () => {
  try {
    JSON.parse(caseAdvancedJson.value || '{}');
  } catch (error) {
    throw new Error('高级自定义字段不是合法JSON');
  }
  const payload = {};
  caseChangedKeys.value.forEach(key => {
    payload[key] = caseManualForm.value?.[key] ?? '';
  });
  return payload;
};

const saveComparableManualDraft = async (silent = false) => {
  if (!editingComparableCase.value) return;
  try {
    const draftFields = buildComparableDraftPayload();
    if (!Object.keys(draftFields).length) {
      if (!silent) showToast('没有新的草稿需要保存。');
      return true;
    }
    const item = await apiJson(`/api/comparable-library/cases/${editingComparableCase.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ manual_draft_fields: draftFields })
    });
    editingComparableCase.value = item;
    caseChangedKeys.value = [];
    caseDraftState.value = '草稿已保存，尚未采用';
    if (!silent) showToast('人工补充草稿已保存，确认采用前不会进入测算和报告。');
    await loadComparableCases();
    return true;
  } catch (error) {
    caseDraftState.value = '草稿保存失败';
    if (!silent) showToast(`保存人工补充草稿失败：${error.message}`, 'error');
    return false;
  }
};

const confirmComparableManualFields = async () => {
  if (!editingComparableCase.value) return;
  try {
    const saved = await saveComparableManualDraft(true);
    if (!saved) return;
    const item = await apiJson(`/api/comparable-library/cases/${editingComparableCase.value.id}/confirm-manual-fields`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    editingComparableCase.value = item;
    caseManualForm.value = { ...(item.manual_fields || {}) };
    caseChangedKeys.value = [];
    refreshCaseAdvancedJson();
    comparableSlots.forEach(slot => {
      if (selectedComparableIds[slot] === item.id) selectedComparableRecords[slot] = item;
    });
    marketAnalysis.value = null;
    form.market_comp_analysis.value = null;
      caseDraftState.value = '已确认采用';
      showToast('人工补充字段已确认采用，请重新计算市场比较法。');
    await loadComparableCases();
  } catch (error) {
    showToast(`确认人工补充失败：{error.message}`, 'error');
  }
};

const caseFieldStatus = (key) => {
  if (Object.prototype.hasOwnProperty.call(editingComparableCase.value?.manual_draft_fields || {}, key) || caseChangedKeys.value.includes(key)) return 'draft';
  if (Object.prototype.hasOwnProperty.call(editingComparableCase.value?.manual_fields || {}, key)) return 'confirmed';
  if (editingComparableCase.value?.[key]) return 'official';
  return 'missing';
};

const caseFieldStatusLabel = (key) => ({
  draft: '人工草稿',
  confirmed: '已确认',
  official: '官网',
  missing: '待补充'
}[caseFieldStatus(key)] || '待补充');

const loadFactorScheme = async () => {
  try {
    const data = await apiJson(`/api/comparable-library/factor-schemes/${schemeUsageKey.value}`);
    factorScheme.value = data;
    factorSchemeBaseline.value = JSON.parse(JSON.stringify(data));
    factorSchemeJson.value = JSON.stringify(data, null, 2);
  } catch (error) {
    showToast(`因子方案载入失败：${error.message}`, 'error');
  }
};

const buildSchemeChangeSummary = () => {
  const before = factorSchemeBaseline.value || {};
  const after = factorScheme.value || {};
  const changes = [];
  if (before.name !== after.name) changes.push(`方案名称：${before.name || '未命名'} → ${after.name || '未命名'}`);
  const beforeFactors = new Map((before.factors || []).map(item => [item.key, item]));
  const afterFactors = new Map((after.factors || []).map(item => [item.key, item]));
  afterFactors.forEach((factor, key) => {
    const old = beforeFactors.get(key);
    if (!old) {
      changes.push(`新增因素：${factor.label || key}`);
      return;
    }
    if (old.label !== factor.label) changes.push(`因素改名：${old.label || key} → ${factor.label || key}`);
    if (Boolean(old.enabled) !== Boolean(factor.enabled)) changes.push(`${factor.label || key}：${factor.enabled ? '启用' : '停用'}`);
    if (Boolean(old.required) !== Boolean(factor.required)) changes.push(`${factor.label || key}：改为${factor.required ? '必填' : '可选'}`);
    if (old.review_status !== factor.review_status) changes.push(`${factor.label || key}：规则状态变更`);
    if (old.source !== factor.source) changes.push(`${factor.label || key}：规则来源变更`);
    if (old.help_text !== factor.help_text) changes.push(`${factor.label || key}：判定说明变更`);
    if (JSON.stringify(old.levels || []) !== JSON.stringify(factor.levels || [])) changes.push(`${factor.label || key}：等级、指数或判定口径变更`);
  });
  beforeFactors.forEach((factor, key) => {
    if (!afterFactors.has(key)) changes.push(`删除因素：${factor.label || key}`);
  });
  return changes;
};

const requestSaveFactorScheme = () => {
  schemeChangeSummary.value = buildSchemeChangeSummary();
  if (!schemeChangeSummary.value.length) {
    showToast('规则方案没有需要保存的变更。');
    return;
  }
  showSchemeChangeDialog.value = true;
};

const saveFactorScheme = async () => {
  try {
    const scheme = factorScheme.value || JSON.parse(factorSchemeJson.value || '{}');
    const data = await apiJson(`/api/comparable-library/factor-schemes/${schemeUsageKey.value}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scheme)
    });
    factorScheme.value = data;
    factorSchemeBaseline.value = JSON.parse(JSON.stringify(data));
    factorSchemeJson.value = JSON.stringify(data, null, 2);
    showSchemeChangeDialog.value = false;
    showToast('全局因子方案已保存；既有报告的冻结快照不受影响。');
  } catch (error) {
    showToast(`保存因子方案失败：${error.message}`, 'error');
  }
};

const applyFactorSchemeJson = () => {
  try {
    factorScheme.value = JSON.parse(factorSchemeJson.value || '{}');
    showToast('JSON 已应用到可视化方案，保存后生效。');
  } catch (error) {
    showToast(`JSON 格式错误：${error.message}`, 'error');
  }
};

const addSchemeFactor = () => {
  if (!factorScheme.value) return;
  factorScheme.value.factors.push({
    key: `manual_${Date.now()}`,
    label: '新增因素',
    group: '区域因素',
    required: true,
    source: 'manual',
    help_text: '',
    levels: [],
    review_status: 'needs_review',
    order: factorScheme.value.factors.length,
    enabled: true
  });
};

const removeSchemeFactor = (key) => {
  if (!factorScheme.value) return;
  factorScheme.value.factors = factorScheme.value.factors.filter(item => item.key !== key);
};

const addSchemeLevel = (factor) => {
  factor.levels = factor.levels || [];
  factor.levels.push({ label: '一般', index: '100', description: '' });
};

const removeSchemeLevel = (factor, index) => {
  factor.levels.splice(index, 1);
};

const marketSubject = () => ({
  valuation_date: isoDateFromParts(parseCnDate(form.valuation_date.value)) || form.valuation_date.value,
  land_usage_key: form.land_usage_key.value,
  land_usage: form.land_usage.value,
  land_area_mode: form.land_area_mode.value,
  land_area: form.land_area.value,
  land_use_term_years: form.land_use_term_years.value,
  land_development_set: form.land_development_set.value,
  right_type: form.right_type.value,
  land_location: form.land_location_full.value || form.land_location.value
});

const applyMarketAnalysisToForm = (data) => {
  marketAnalysis.value = data;
  marketMonthlyGrowthRate.value = data.monthly_growth_rate || '0.13';
  marketLandReductionRate.value = data.land_reduction_rate || '5.4';
  form.market_comp_analysis.value = data;
  form.market_comp_price.value = data.market_comp_price || '';
  form.market_comp_price.origin = 'generated';
  form.comparable_case_count.value = data.selected_cases?.length || 0;
  (data.selected_cases || []).forEach((item, index) => {
    const slot = comparableSlots[index];
    selectedComparableRecords[slot] = item;
    selectedComparableIds[slot] = item.id;
  });
  [
    'market_comp_step1_instances', 'market_comp_basic_rows', 'market_comp_factor_condition_rows', 'market_comp_time_index_rows',
    'market_comp_factor_index_rows', 'market_comp_correction_rows', 'market_comp_step4_solve',
    'market_comp_comparable_basis', 'market_comp_factor_selection', 'market_comp_condition_intro',
    'market_comp_index_basis', 'market_comp_verification'
  ].forEach(key => {
    if (form[key]) form[key].value = data[key] ?? form[key].value;
  });
};

const calculateMarketComparison = async () => {
  const caseIds = comparableSlots.map(slot => selectedComparableIds[slot]);
  if (caseIds.some(value => !value)) {
    showToast('请先固定选择三宗比较实例 A/B/C。', 'warning');
    return;
  }
  try {
    const analysis = marketAnalysis.value ? JSON.parse(JSON.stringify(marketAnalysis.value)) : {};
    analysis.subject = marketSubject();
    analysis.case_ids = caseIds;
    analysis.monthly_growth_rate = marketMonthlyGrowthRate.value;
    analysis.land_reduction_rate = marketLandReductionRate.value;
    analysis.evidence_snapshot_ids = form.market_comp_evidence_snapshot_ids.value || [];
    const data = await apiJson('/api/market-comparison/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analysis })
    });
    applyMarketAnalysisToForm(data);
    if (activeTab.value === 'p5') await loadValuationProcessDraft();
    showToast(data.complete ? `市场比较法计算完成：${data.market_comp_price} 元/㎡` : '已计算建议结果，仍有必填因子待确认。', data.complete ? 'success' : 'warning');
  } catch (error) {
    showToast(`市场比较法计算失败：${error.message}`, 'error');
  }
};

watch(
  () => valuationMethodOptions.map(item => Boolean(form[item.flag]?.value)),
  () => {
    if (activeTab.value === 'p5') loadValuationProcessDraft();
  }
);

const marketCalculation = (slot) => (marketAnalysis.value?.calculations || []).find(item => item.slot === slot);

const factorSourceLabel = (source) => ({
  official: '官网',
  calculated: '系统计算',
  scheme: '方案建议',
  manual: '人工判断',
  override: '人工覆盖'
}[source] || '人工判断');

const factorConfirmedCount = (factor) => comparableSlots.filter(slot => (
  factor.cases?.[slot]?.confirmed && String(factor.cases?.[slot]?.index || '').trim()
)).length;

const factorMissingIndexCount = (factor) => comparableSlots.filter(slot => (
  !String(factor.cases?.[slot]?.index || '').trim()
)).length;

const openFactorGuide = (factor) => {
  if (activeFactorGuide.value && activeFactorGuide.value.factor.key !== factor.key && !closeFactorGuide()) return;
  activeFactorGuide.value = { factor };
  factorGuideSnapshot.value = JSON.parse(JSON.stringify(factor));
  factorGuideDirty.value = false;
};

const markFactorGuideDirty = () => {
  comparableSlots.forEach(slot => {
    if (activeFactorGuide.value?.factor.cases?.[slot]) activeFactorGuide.value.factor.cases[slot].confirmed = false;
  });
  factorGuideDirty.value = true;
};

const markMarketCalculationParameter = (key, valueRef) => {
  if (!marketAnalysis.value) marketAnalysis.value = {};
  marketAnalysis.value[key] = valueRef.value;
  form.market_comp_analysis.value = marketAnalysis.value;
  markFactorGuideDirty();
};

const onComparableBasisStatusChange = async () => {
  if (marketComparableBasisStatus.value === 'needs_adjustment') {
    marketWorkspaceView.value = 'narratives';
    showToast('已标记为需要调整，请在“正文与表格”中修改建立价格可比基础段落。', 'warning');
  }
  await loadValuationProcessDraft();
};

const applyFactorLevel = (level, slot) => {
  if (!activeFactorGuide.value) return;
  const { factor } = activeFactorGuide.value;
  const item = factor.cases[slot];
  item.value = level.label;
  item.level_label = level.label;
  item.index = level.index;
  item.source = 'scheme';
  item.override_reason = '';
  item.confirmed = false;
  markFactorGuideDirty();
};

const markActiveFactorOverride = (slot) => {
  if (!activeFactorGuide.value) return;
  const { factor } = activeFactorGuide.value;
  factor.cases[slot].source = 'override';
  factor.cases[slot].confirmed = false;
  markFactorGuideDirty();
};

const confirmActiveFactor = () => {
  if (!activeFactorGuide.value) return;
  const { factor } = activeFactorGuide.value;
  if (!activeFactorCanConfirm.value) {
    showToast('请先为实例 A/B/C 填写有效指数。', 'warning');
    return;
  }
  comparableSlots.forEach(slot => {
    factor.cases[slot].confirmed = true;
  });
  factor.review_status = 'confirmed';
  form.market_comp_analysis.value = marketAnalysis.value;
  factorGuideDirty.value = false;
  showToast(`“${factor.label}”的实例 A/B/C 已一次确认，请重新计算。`);
  activeFactorGuide.value = null;
  factorGuideSnapshot.value = null;
};

const closeFactorGuide = () => {
  if (!activeFactorGuide.value) return true;
  if (factorGuideDirty.value && !window.confirm('当前因素有尚未确认的修改，是否放弃修改并关闭？')) return false;
  if (factorGuideDirty.value && factorGuideSnapshot.value) {
    Object.keys(activeFactorGuide.value.factor).forEach(key => delete activeFactorGuide.value.factor[key]);
    Object.assign(activeFactorGuide.value.factor, JSON.parse(JSON.stringify(factorGuideSnapshot.value)));
  }
  activeFactorGuide.value = null;
  factorGuideSnapshot.value = null;
  factorGuideDirty.value = false;
  return true;
};

const generateComparableEvidence = async () => {
  const caseIds = comparableSlots.map(slot => selectedComparableIds[slot]);
  if (caseIds.some(value => !value)) return;
  isLoading.value = true;
  loadingMessage.value = '正在生soffice.com 生成成交公告证据 PDF 与图片..';
  try {
    const snapshots = await apiJson('/api/comparable-library/evidence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_ids: caseIds })
    });
    const ids = snapshots.map(item => item.snapshot_id);
    marketEvidenceSnapshots.value = snapshots;
    form.market_comp_evidence_snapshot_ids.value = ids;
    if (marketAnalysis.value) {
      marketAnalysis.value.evidence_snapshot_ids = ids;
      form.market_comp_analysis.value = marketAnalysis.value;
    }
    if (activeTab.value === 'p5') await loadValuationProcessDraft();
      showToast('三宗成交公告证据已生成并冻结。');
  } catch (error) {
      showToast(`证据生成失败：${error.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

// 4. 视觉状态机辅助函数
const getInputClass = (key) => {
  const field = form[key];
  if (!field) return '';
  if (field.is_dirty) return '';
  if (field.origin === 'excel_imported') return 'origin-excel';
  if (field.origin === 'ocr_extracted') return 'origin-ocr';
  return '';
};

const computedHotspotPatterns = [
  /_price$/,
  /\.totals\./,
  /\.usage_results\./,
  /\.income_results\./,
  /\.rent_calculations\.[^.]+\.corrected_monthly_rent$/,
  /\.attachment_compensation_analysis\./,
  /\.building_compensation_rows\.\d+\.amount$/,
  /\.resettlement_population_cases\.\d+\.population_per_ha$/,
  /\.acquisition_items\.[^.]+\.amount_per_sqm$/,
  /\.tax_items\.[^.]+\.amount_per_sqm$/,
  /\.development_items\.[^.]+\.amount_per_sqm$/,
  /\.correction_factor$/,
  /\.corrected_price$/,
  /\.adjusted_price$/,
  /\.comparison_results\./,
  /\.calculation_results\./,
  /\.results\./,
];
const isComputedHotspotField = (field) => {
  const text = String(field || '');
  if (!text) return false;
  return computedHotspotPatterns.some(pattern => pattern.test(text));
};

const segmentFields = (seg) => {
  const fields = [];
  if (seg?.field) fields.push(seg.field);
  if (Array.isArray(seg?.fields)) fields.push(...seg.fields);
  return fields;
};

const getDocRefClass = (seg) => [
  'doc-ref-span',
  {
    'prompt-ref-span': (seg?.text || '').includes('【请填写'),
    'computed-ref-span': segmentFields(seg).some(isComputedHotspotField)
  },
];

const showBadge = (key) => {
  const field = form[key];
  return field && field.origin !== 'manual' && field.origin !== 'generated' && !field.is_dirty;
};

const getBadgeClass = (key) => {
  const field = form[key];
  if (!field) return '';
  if (field.origin === 'excel_imported') return 'excel';
  if (field.origin === 'ocr_extracted') return 'ocr';
  if (field.origin === 'generated') return 'generated';
  return '';
};

const getBadgeText = (key) => {
  const field = form[key];
  if (!field) return '';
  if (field.origin === 'excel_imported') return '📊 测算表';
  if (field.origin === 'ocr_extracted') return '📷 证照识别';
  if (field.origin === 'generated') return '🧠 智能生成';
  return '';
};

const hasUsefulValue = (value) => {
  if (value === null || value === undefined) return false;
  const text = String(value).trim();
  return text !== '' && text !== '______';
};

const applyFieldValue = (key, value, origin = 'ocr_extracted') => {
  if (!form[key] || !hasUsefulValue(value)) return false;
  form[key].value = value;
  form[key].origin = origin;
  form[key].is_dirty = false;
  return true;
};

// 🧹 V6.2 附件文件名清洗函数
const cleanFileName = (name) => {
  if (!name) return '';
  let clean = name.replace(/\.(pdf|docx|txt|png|jpg|jpeg|bmp|tif|tiff|webp)$/i, '');
  clean = clean.replace(/(_|\-)?副本/g, '');
  clean = clean.replace(/(_|\-|\()?\d+(\))?$/g, '');
  return clean.trim();
};

const handleSitePhotoUpload = async (event) => {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;
  const availableSlots = Math.max(0, 6 - sitePhotoItems.value.length);
  const accepted = files.filter(file => file.type.startsWith('image/')).slice(0, availableSlots);
  if (accepted.length < files.length) {
    showToast('现场照片最多保留 6 张，非图片文件已忽略。', 'warning');
  }

  const readAsDataUrl = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  for (const file of accepted) {
    try {
      const dataUrl = await readAsDataUrl(file);
      const idx = sitePhotoItems.value.length + 1;
      sitePhotoItems.value.push({
        id: `${Date.now()}_${idx}_${file.name}`,
        name: file.name,
        dataUrl,
        caption: `图${idx} 估价对象利用现状照片`
      });
    } catch (err) {
      showToast(`读取图片失败：{file.name}`, 'error');
    }
  }
  event.target.value = '';
};

const removeSitePhoto = (idx) => {
  sitePhotoItems.value.splice(idx, 1);
  sitePhotoItems.value.forEach((item, index) => {
    if (!item.caption || /^图\d+ 估价对象利用现状照片$/.test(item.caption)) {
      item.caption = `图${index + 1} 估价对象利用现状照片`;
    }
  });
};

const hasOldValue = (value) => {
  if (value === null || value === undefined) return false;
  const text = String(value).trim();
  return text !== '' && text !== '______';
};

const hasConflict = (item) => {
  const fieldObj = form[item.field];
  if (!fieldObj) return false;
  const oldVal = fieldObj.value;
  const newVal = item.value;
  const isDirty = fieldObj.is_dirty;
  const hasOld = hasOldValue(oldVal);
  return isDirty || (hasOld && oldVal !== newVal);
};

const queueExtractedEvidence = (extracted, source = 'ocr_extracted', rawFileName = '') => {
  let count = 0;
  const cleanedName = cleanFileName(rawFileName);
  const matchedTabs = new Set();

  Object.keys(extracted || {}).forEach(key => {
    const value = extracted[key];
    if (form[key] && hasUsefulValue(value)) {
      const fieldObj = form[key];
      const oldValue = fieldObj.value;
      const isDirty = fieldObj.is_dirty;
      const hasOld = hasOldValue(oldValue);
      const isSame = oldValue === value;
      
      // is_dirty 保护策略：已有人工修改或非空旧值不同的字段，默认取消勾选
      let checked = true;
      if (isDirty || (hasOld && !isSame)) {
        checked = false;
      }

      ocrEvidencePool.value.push({
        id: `${Date.now()}_${key}_${count}`,
        field: key,
        label: FIELD_REGISTRY[key]?.label || key,
        oldValue: oldValue,
        value: value,
        source: source,
        checked: checked,
        isDirty: isDirty,
        fileName: cleanedName
      });
      matchedTabs.add(FIELD_REGISTRY[key]?.tab || 'p3');
      count++;
    }
  });
  if (count > 0) {
    showOCR.value = true;
    activeTab.value = matchedTabs.has('p4') ? 'p4' : 'p3';
  }
  return count;
};

const applyExtractedFields = (extracted, origin = 'ocr_extracted', rawFileName = '') => {
  return queueExtractedEvidence(extracted, origin, rawFileName);
};

const DOC_FIELD_KEYS = new Set([
  'basis_docs_list',
  'valuation_basis_docs_list',
  'gov_approval_name',
  'proof_doc_name',
  'house_cert_name',
  'area_docs_desc_name',
  'land_cert_name',
  'registered_proof_docs',
  'entrusted_source_docs'
]);

const isBasisDocCandidate = (item) => {
  const value = String(item?.value || '');
  return DOC_FIELD_KEYS.has(item?.field) || /批复|纪要|合同|证明|审批|规划条件|不动产权证书|房屋所有权证|土地使用权证/.test(value);
};

const appendBasisDocValue = (value, origin = 'ocr_extracted') => {
  const incoming = String(value || '').trim();
  if (!incoming) return false;
  const current = String(form.basis_docs_list.value || '').trim();
  const lines = current ? current.split(/\n+/).map(line => line.trim()).filter(Boolean) : [];
  if (!lines.includes(incoming)) {
    lines.push(incoming);
  }
  form.basis_docs_list.value = lines.join('\n');
  form.basis_docs_list.origin = origin;
  form.basis_docs_list.is_dirty = false;
  regenerateOwnershipDraft(false);
  return true;
};

const injectEvidenceToBasisDocs = (idx) => {
  const item = ocrEvidencePool.value[idx];
  if (!item) return;
  appendBasisDocValue(item.value, item.source);
  ocrEvidencePool.value.splice(idx, 1);
  showToast('已注入依据文件清单，权属草稿将按新依据刷新。');
};

const refreshAfterEvidenceApply = (keys = []) => {
  const tabs = new Set(keys.map(key => FIELD_REGISTRY[key]?.tab).filter(Boolean));
  if (tabs.has('p4')) {
    activeTab.value = 'p4';
    regenerateValuationNarratives(false);
  }
  if (tabs.has('p3')) {
    activeTab.value = tabs.has('p4') ? activeTab.value : 'p3';
    regenerateOwnershipDraft(false);
  }
};

const applyEvidenceToField = (idx) => {
  const item = ocrEvidencePool.value[idx];
  if (!item) return;
  
  if (hasConflict(item)) {
    if (!confirm(`警告：表单中字段“${item.label}”已被人工修改或已含有旧值，继续覆盖将丢失当前值。确认覆盖吗？`)) {
      return;
    }
  }

  if (applyFieldValue(item.field, item.value, item.source)) {
    ocrEvidencePool.value.splice(idx, 1);
    refreshAfterEvidenceApply([item.field]);
    showToast(`已覆盖字段：${item.label}`);
  }
};

// 🧹 V6.2 附件文件名智能依据文件清单注入
const applyFileNameToField = (idx) => {
  const item = ocrEvidencePool.value[idx];
  if (!item || !item.fileName) return;
  
  const currentVal = String(form.basis_docs_list.value || '').trim();
  const cleanedFile = item.fileName.trim();
  
  // 智能去重防止重复追加
  if (currentVal.split('\n').map(x => x.trim()).includes(cleanedFile)) {
    showToast('该文件名已存在于依据清单中', 'warning');
    ocrEvidencePool.value.splice(idx, 1);
    return;
  }
  
  const newVal = currentVal ? `${currentVal}\n${cleanedFile}` : cleanedFile;
  form.basis_docs_list.value = newVal;
  form.basis_docs_list.origin = item.source;
  form.basis_docs_list.is_dirty = false;
  
  showToast(`已成功将文件名清洗值追加至依据文件清单`);
  ocrEvidencePool.value.splice(idx, 1);
  regenerateOwnershipDraft(false);
};

const importUploadedAttachmentsToBasisDocs = () => {
  if (uploadedAttachments.value.length === 0) {
    showToast('当前未成功解析任何附件，请先在右侧上传并解析附件文件', 'warning');
    return;
  }
  const currentVal = String(form.basis_docs_list.value || '').trim();
  const currentLines = currentVal ? currentVal.split(/\n+/).map(x => x.trim()).filter(Boolean) : [];
  let addedCount = 0;
  uploadedAttachments.value.forEach(att => {
    if (!currentLines.includes(att.cleanedName)) {
      currentLines.push(att.cleanedName);
      addedCount++;
    }
  });
  if (addedCount > 0) {
    form.basis_docs_list.value = currentLines.join('\n');
    form.basis_docs_list.origin = 'ocr_extracted';
    form.basis_docs_list.is_dirty = false;
    showToast(`已成功将 ${addedCount} 份已解析的附件文件名追加至依据清单！`);
    regenerateOwnershipDraft(false);
  } else {
    showToast('所有解析的附件名已存在于依据清单中', 'info');
  }
};

const toggleSelectAll = (select) => {
  ocrEvidencePool.value.forEach(item => {
    item.checked = select;
  });
};

const applyBulkOcrInjections = () => {
  const checkedItems = ocrEvidencePool.value.filter(item => item.checked);
  if (checkedItems.length === 0) {
    showToast('⚠ 请先勾选要注入的字段项', 'warning');
    return;
  }

  const conflictFields = checkedItems.filter(item => hasConflict(item));
  if (conflictFields.length > 0) {
    const labels = conflictFields.map(item => item.label).join('、');
    if (!confirm(`警告：您勾选了已被人工修改或已含有旧值的字段（${labels}），继续注入将覆盖这些人工数据。确定要覆盖注入吗？`)) {
      return;
    }
  }

  let count = 0;
  const appliedKeys = [];
  const remainingItems = [];
  ocrEvidencePool.value.forEach(item => {
    if (item.checked) {
      if (applyFieldValue(item.field, item.value, item.source)) {
        appliedKeys.push(item.field);
        count++;
      } else {
        remainingItems.push(item);
      }
    } else {
      remainingItems.push(item);
    }
  });

  ocrEvidencePool.value = remainingItems;
  if (count > 0) {
    refreshAfterEvidenceApply(appliedKeys);
    showToast(`🎉 成功一键注入 ${count} 个字段到表单中！`);
  }
};

const discardEvidence = (idx) => {
  ocrEvidencePool.value.splice(idx, 1);
};

// 键盘敲击，主权瞬间秒级收归人工！背景变白，微章隐去！
const syncLandUseTermYearsFromTerm = () => {
  const raw = String(form.land_use_term?.value ?? '');
  const matched = raw.match(/\d+(?:\.\d+)?/);
  const years = matched ? matched[0] : '';
  if (!form.land_use_term_years) return;
  if (form.land_use_term_years.value === years) return;
  form.land_use_term_years.value = years;
  form.land_use_term_years.origin = 'manual';
  form.land_use_term_years.is_dirty = true;
};

const onFieldInput = (key) => {
  const field = form[key];
  if (field) {
    field.is_dirty = true;
    field.origin = 'manual';
  }

  if (key === 'land_use_term') {
    syncLandUseTermYearsFromTerm();
  }

  if (['use_cost_approx', 'use_market_comp', 'use_income_cap', 'use_residual', 'use_benchmark_corr'].includes(key)) {
    ensureMethodWeights();
  }

  if (['valuation_date', 'base_price_base_date', 'base_price_publish_date', 'base_price_disable_threshold_years_text'].includes(key)) {
    syncBasePriceExpiryFields();
  }

  if (['county_name', 'land_location', 'land_plot_number'].includes(key)) {
    scheduleCostZoneRematch();
  }

  // 如果是确价测算或可选证据链的相关字段被修改，静默刷新证据预警
  const triggerKeys = [
    'use_cost_approx', 'use_market_comp', 'use_income_cap', 'use_residual', 'use_benchmark_corr',
    'valuation_basis_docs_list', 'weight_logic_type', 'method_weight_percentages',
    'cost_approx_price', 'market_comp_price', 'income_cap_price', 'benchmark_corr_price', 'residual_price',
    'comparable_case_count', 'case_similarity_level', 'case_time_valid', 'market_activity_level',
    'has_stable_income_data', 'income_can_be_separated', 'rent_market_activity_level', 'cap_rate_source_available',
    'has_development_plan', 'development_value_measurable', 'construction_cost_available', 'sales_or_rent_forecast_reliable',
    'has_land_acquisition_cost_docs', 'has_development_cost_docs', 'cost_data_reliable', 'cost_market_gap_risk',
    'base_price_in_coverage', 'base_price_has_applicable_use',
    'base_price_doc_no', 'base_price_doc_name', 'base_price_publish_date', 'base_price_base_date', 'base_price_doc_authority',
    'base_price_rule_doc_name', 'base_price_rule_doc_no', 'base_price_update_cycle_years_text', 'base_price_disable_threshold_years_text'
  ];
  if (triggerKeys.includes(key)) {
    updateMethodWarnings();
  }
};

const onBasisDocsInput = () => {
  onFieldInput('basis_docs_list');
};

const inferLandUsageKey = (value) => {
  const usage = String(value || '').trim();
  if (!usage) return form.land_usage_key?.value || 'residential';
  const direct = landUsageOptions.find(item => item.key !== 'other' && (item.label === usage || item.report === usage));
  if (direct) return direct.key;
  const matched = landUsageOptions.find(item => item.key !== 'other' && item.keywords.some(keyword => usage.includes(keyword)));
  return matched?.key || 'other';
};

const syncLandUsageFields = () => {
  let key = form.land_usage_key?.value;
  if (!landUsageByKey[key]) {
    key = inferLandUsageKey(form.land_usage?.value || form.land_usage_short?.value || form.land_usage_full?.value);
    form.land_usage_key.value = key;
  }
  const option = landUsageByKey[key] || landUsageByKey.residential;
  const usage = key === 'other'
    ? String(form.land_usage_other?.value || form.land_usage?.value || '').trim()
    : option.report;
  if (!usage) return;
  form.land_usage.value = usage;
  form.land_usage_short.value = usage;
  form.land_usage_full.value = usage;
  form.land_usage_current_class.value = key === 'other' ? usage : option.currentClass;
  form.land_usage_price_class.value = key === 'other' ? usage : option.priceClass;
  ['land_usage', 'land_usage_short', 'land_usage_full', 'land_usage_current_class', 'land_usage_price_class'].forEach(fieldKey => {
    form[fieldKey].origin = 'generated';
    form[fieldKey].is_dirty = false;
  });
  if (form.asset_use_category && option.category) {
    form.asset_use_category.value = option.category;
    form.asset_use_category.origin = 'generated';
    form.asset_use_category.is_dirty = false;
  }
  if (form.asset_use_category_other) {
    form.asset_use_category_other.value = key === 'other' ? usage : '';
    form.asset_use_category_other.origin = 'generated';
    form.asset_use_category_other.is_dirty = false;
  }
};

const syncLegacyLandUsageFields = syncLandUsageFields;

const onLandUsageKeyChange = () => {
  if (form.land_usage_key.value !== 'other') {
    form.land_usage_other.value = '';
  }
  syncLandUsageFields();
  onFieldInput('land_usage_key');
  form.land_usage.origin = 'generated';
  form.land_usage.is_dirty = false;
};

const onLandUsageOtherInput = () => {
  syncLandUsageFields();
  onFieldInput('land_usage_other');
  form.land_usage.origin = 'generated';
  form.land_usage.is_dirty = false;
};

const syncBasePriceExpiryFields = () => {
  const years = basePriceElapsedYears.value;
  const expired = years !== null && years > basePriceDisableThreshold.value;
  ['base_price_is_expired', 'is_base_price_expired'].forEach(key => {
    if (form[key]) {
      form[key].value = expired;
      form[key].origin = 'generated';
      form[key].is_dirty = false;
    }
  });
};

const buildPlotRatioDisplay = () => {
  const mode = form.plot_ratio_mode?.value || 'range';
  const value = String(form.plot_ratio?.value || '').trim();
  const min = String(form.plot_ratio_min?.value || '').trim();
  return mode === 'range' && min ? `${min}-${value}` : value;
};

const syncPlotRatioDisplay = (force = false) => {
  if (!form.plot_ratio_display) return;
  if (force || !form.plot_ratio_display.is_dirty) {
    form.plot_ratio_display.value = buildPlotRatioDisplay();
    form.plot_ratio_display.origin = form.plot_ratio.origin;
    form.plot_ratio_display.is_dirty = false;
  }
};

const onPlotRatioInput = (key) => {
  onFieldInput(key);
  syncPlotRatioDisplay(true);
};

const buildSetPlotRatioDisplay = () => {
  const mode = form.set_plot_ratio_mode?.value || 'fixed';
  const value = String(form.set_plot_ratio?.value || '').trim();
  const min = String(form.set_plot_ratio_min?.value || '').trim();
  return mode === 'range' && min ? `${min}-${value}` : value;
};

const syncSetPlotRatioDisplay = (force = false) => {
  if (!form.set_plot_ratio_display) return;
  if (force || !form.set_plot_ratio_display.is_dirty) {
    form.set_plot_ratio_display.value = buildSetPlotRatioDisplay();
    form.set_plot_ratio_display.origin = form.set_plot_ratio.origin;
    form.set_plot_ratio_display.is_dirty = false;
  }
};

const onSetPlotRatioInput = (key) => {
  onFieldInput(key);
  syncSetPlotRatioDisplay(true);
};

const textValue = (key, fallback = '') => {
  const value = form[key]?.value;
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'object') return value;
  const text = String(value).trim();
  return text && text !== '______' ? text : fallback;
};

const buildFlatPayload = () => {
  syncLegacyLandUsageFields();
  syncPlotRatioDisplay(true);
  syncSetPlotRatioDisplay(true);
  syncBasePriceExpiryFields();
  form.show_price_in_text.value = true;
  form.show_price_in_text.origin = 'generated';
  form.show_price_in_text.is_dirty = false;
  form.explain_unselected_methods.value = true;
  form.explain_unselected_methods.origin = 'generated';
  form.explain_unselected_methods.is_dirty = false;
  const payload = {};
  Object.keys(form).forEach(key => {
    payload[key] = textValue(key);
  });
  payload.plot_ratio_display = buildPlotRatioDisplay();
  payload.set_plot_ratio_display = buildSetPlotRatioDisplay();
  payload.cost_approx_analysis = costAnalysis.value;
  return payload;
};

const processStatusLabel = (status) => ({
  complete: '已完成',
  incomplete: '待完成',
  skeleton: '骨架待完善'
}[status] || '待校核');

const processNarrative = (method, key) => method?.narratives?.find(item => item.key === key);
const processTable = (method, key) => method?.tables?.find(item => item.key === key);
const processResult = (method, key) => method?.results?.find(item => item.key === key);
const processContentBlocks = (method) => {
  if (method?.content_blocks?.length) return method.content_blocks;
  return [
    ...(method?.narratives || []).map(item => ({ type: 'narrative', key: item.key })),
    ...(method?.tables || []).map(item => ({ type: 'table', key: item.key })),
    ...(method?.results || []).map(item => ({ type: 'result', key: item.key }))
  ];
};
const processBlockRenderable = (method, block) => (
  (block?.type === 'narrative' && processNarrative(method, block.key))
  || (block?.type === 'table' && processTable(method, block.key))
  || (block?.type === 'result' && processResult(method, block.key))
);
const processRenderableContentBlocks = (method) => processContentBlocks(method).filter(block => processBlockRenderable(method, block));
const processBlockAnchorId = (block) => `process_block_${sourceKeyFragment(`${block?.type || 'block'}_${block?.key || ''}`)}`;
const processBlockNavLabel = (method, block) => {
  if (!block) return '正文块';
  if (block.type === 'narrative') return processNarrative(method, block.key)?.title || block.key;
  if (block.type === 'table') return processTable(method, block.key)?.report_title || processTable(method, block.key)?.title || block.key;
  if (block.type === 'result') return processResult(method, block.key)?.label || '计算结果';
  return block.key || '正文块';
};
const scrollToProcessBlock = (block) => {
  const target = document.getElementById(processBlockAnchorId(block));
  target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};
const processTableKeys = (columnCount) => {
  if (columnCount === 4) return ['label', 'a', 'b', 'c'];
  if (columnCount === 5) return ['label', 'subject', 'a', 'b', 'c'];
  if (columnCount === 6) return ['group', 'subgroup', 'label', 'a', 'b', 'c'];
  return ['group', 'subgroup', 'label', 'subject', 'a', 'b', 'c'];
};
const processTableHeaderRows = (table) => (
  table?.header_rows?.length
    ? table.header_rows
    : [(table?.columns || []).map(label => ({ label, colspan: 1, rowspan: 1 }))]
);
const processTableHeaderCellLabel = (cell) => cell?.label ?? cell?.text ?? cell?.value ?? '';
const processNarrativeSegments = (section) => {
  if (section?.segments?.length) return section.segments;
  const text = String(section?.effective_text || '');
  return text ? [{ text }] : [];
};
const processTableDisplayRows = (table) => {
  const columns = table?.columns || [];
  const fallbackKeys = processTableKeys(columns.length || 0);
  const groupColumns = table?.group_columns || [];
  const rows = (table?.rows || []).map(item => {
    const refs = item?.cell_refs || [];
    const explicitCells = item?.cells?.length ? item.cells : null;
    const cells = (explicitCells || columns.map((column, index) => (
      item?.[column] ?? item?.[fallbackKeys[index]] ?? (groupColumns.includes(index) ? '' : '待校核')
    ))).map((value, index) => {
      const cell = value && typeof value === 'object' && !Array.isArray(value) ? value : { value };
      return {
        value: cell.value ?? cell.label ?? cell.text ?? '',
        ref: cell.ref || refs[index] || '',
        rowspan: Number(cell.rowspan || 1),
        colspan: Number(cell.colspan || 1),
        hidden: Boolean(cell.hidden)
      };
    });
    const firstText = String(cells[0]?.value || '').trim();
    const restEmpty = cells.slice(1).every(cell => !String(cell?.value || '').trim());
    if (firstText.startsWith('注') && restEmpty && cells.length > 1) {
      cells[0].colspan = cells.length;
      cells.slice(1).forEach(cell => { cell.hidden = true; });
    }
    return cells;
  });
  if ((table?.rows || []).some(item => item?.cells?.length)) {
    return rows;
  }
  groupColumns.forEach(columnIndex => {
    let start = 0;
    while (start < rows.length) {
      const value = String(rows[start]?.[columnIndex]?.value || '');
      let end = start;
      while (value && end + 1 < rows.length && String(rows[end + 1]?.[columnIndex]?.value || '') === value) end += 1;
      if (value && end > start) {
        rows[start][columnIndex].rowspan = end - start + 1;
        for (let index = start + 1; index <= end; index += 1) rows[index][columnIndex].hidden = true;
      }
      start = end + 1;
    }
  });
  return rows;
};

const processTableActionLabel = (table) => {
  const target = String(table?.source_target || '');
  if (target === 'library') return '前往实例库';
  if (target.startsWith('cost')) return '前往成本法测算';
  if (target.startsWith('benchmark_')) return '前往基准地价校核';
  if (target.startsWith('income_')) return '前往收益法校核';
  return '前往因素分析';
};

const syncProcessNarrativesToForm = (draft) => {
  (draft?.methods || []).forEach(method => {
    (method?.narratives || []).forEach(section => {
      if (form[section.key]) {
        form[section.key].value = section.effective_text || '';
        form[section.key].origin = section.override_text !== null ? 'manual' : 'generated';
        form[section.key].is_dirty = section.override_text !== null;
      }
    });
  });
};

const costConfirmedCount = (key) => (
  (costAnalysis.value?.[key] || []).filter(item => item.enabled !== false && item.confirmed).length
);

const visibleCostItems = (key) => (
  (costAnalysis.value?.[key] || []).filter(item => item.key !== 'ground_attachment')
);

const confirmEnabledItems = (items = []) => {
  (items || []).filter(item => item.enabled !== false).forEach(item => {
    item.confirmed = true;
  });
};

const confirmCostPolicies = () => confirmEnabledItems(costAnalysis.value?.policy_documents || []);
const costSystemPolicies = computed(() => (costAnalysis.value?.policy_documents || []).filter(item => item.source_type === 'system_recommendation'));
const costAdoptedPolicies = computed(() => (costAnalysis.value?.policy_documents || []).filter(item => item.enabled !== false));
const costSupplementalPolicies = computed(() => costAdoptedPolicies.value.filter(item => item.role === 'supplemental'));
const addCostPolicyDocument = () => {
  const draft = costPolicyDraft.value || {};
  if (!String(draft.name || draft.reference_text || '').trim()) {
    showToast('请先填写或引用政策依据', 'warning');
    return;
  }
  costAnalysis.value.policy_documents ||= [];
  const key = `manual_policy_${Date.now()}`;
  const replacementTarget = String(draft.replaces_key || '').trim();
  costAnalysis.value.policy_documents.push({
    ...JSON.parse(JSON.stringify(draft)),
    key,
    name: String(draft.name || draft.reference_text || '').trim(),
    enabled: true,
    applicable: true,
    confirmed: false,
    valuation_date: form.valuation_date.value,
    source_type: draft.source_type || 'manual'
  });
  if (replacementTarget) {
    const target = costAnalysis.value.policy_documents.find(item => item.key === replacementTarget);
    if (target) target.enabled = false;
    const affected = {
      province_compensation: ['land_compensation'],
      local_compensation: ['ground_attachment'],
      tax_policy: (costAnalysis.value.tax_items || []).map(item => item.key)
    }[draft.role] || [];
    ['acquisition_items', 'tax_items', 'development_items'].forEach(group => {
      (costAnalysis.value[group] || []).forEach(item => {
        if (affected.includes(item.key)) {
          item.confirmed = false;
          item.policy_key = key;
          item.standard_value = '';
          item.coefficient = '';
          item.amount_per_sqm = '';
        }
      });
    });
  }
  costPolicyDraft.value = { name: '', document_no: '', region: '湖南省', publish_date: '', effective_date: '', role: 'supplemental', source_type: 'manual', reference_text: '', replaces_key: '', note: '' };
  showToast(replacementTarget ? '已加入替换政策，相关费用已转为待校核' : '已加入补充依据', 'success');
};
const applyCostPolicyReference = (value) => {
  const selected = String(value || '').trim();
  if (!selected) return;
  costPolicyDraft.value.reference_text = selected;
  if (!costPolicyDraft.value.name) costPolicyDraft.value.name = selected;
  costPolicyDraft.value.source_type = 'shared_reference';
};
const confirmCostGroup = (key) => confirmEnabledItems(costAnalysis.value?.[key] || []);
const confirmCostBuildingCompensation = () => confirmEnabledItems(costAnalysis.value?.building_compensation_rows || []);
const confirmCostPopulationCases = () => confirmEnabledItems(costAnalysis.value?.resettlement_population_cases || []);
const confirmCostDevelopmentSurveyCases = () => confirmEnabledItems(costAnalysis.value?.development_survey_cases || []);
const confirmCostScenarios = () => confirmEnabledItems(costAnalysis.value?.usage_scenarios || []);
const confirmCostRiskItems = () => confirmEnabledItems(costAnalysis.value?.risk_items || []);
const confirmCostRiskGroups = () => confirmEnabledItems(costAnalysis.value?.risk_groups || []);
const confirmCostLocationFactors = () => {
  confirmEnabledItems((costAnalysis.value?.location_factors || []).filter(item => item?.enabled !== false));
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const addCostPopulationCase = () => {
  costAnalysis.value.resettlement_population_cases ||= [];
  costAnalysis.value.resettlement_population_cases.push({
    key: `case_${Date.now()}`,
    name: '',
    location: '',
    land_area_ha: '',
    population: '',
    population_per_ha: '',
    confirmed: false
  });
};

const addCostDevelopmentSurveyCase = () => {
  costAnalysis.value.development_survey_cases ||= [];
  costAnalysis.value.development_survey_cases.push({
    key: `survey_${Date.now()}`,
    name: '',
    location: '',
    survey_date: '',
    source_type: '',
    development_set: '',
    total_per_sqm: '',
    source_unit: '',
    note: '',
    confirmed: false
  });
};

const onCostDevelopmentSurveyInput = (item) => {
  if (item) item.confirmed = false;
};

const costDevelopmentSurveyAverage = computed(() => {
  const values = (costAnalysis.value?.development_survey_cases || [])
    .filter(item => item.confirmed)
    .map(item => parseCostNumber(item.total_per_sqm))
    .filter(value => Number.isFinite(value) && value > 0);
  if (!values.length) return costAnalysis.value?.development_survey_analysis?.average_total_per_sqm || '';
  return formatCostNumber(values.reduce((sum, value) => sum + value, 0) / values.length);
});

const costDevelopmentSurveyStatusLabel = computed(() => {
  const status = costAnalysis.value?.development_survey_analysis?.status || 'pending';
  if (status === 'ready') return '资料充足';
  if (status === 'insufficient') return '资料不足';
  return '待调查';
});

const costDevelopmentSurveyStatusHint = computed(() => {
  const status = costAnalysis.value?.development_survey_analysis?.status || 'pending';
  if (status === 'ready') return '已确认≥3组';
  if (status === 'insufficient') return '建议补足至3组';
  return '请录入调查案例';
});

const paidLandUseGradeOptions = ['一等', '二等', '三等', '四等', '五等', '六等', '七等', '八等', '九等', '十等', '十一等', '十二等', '十三等', '十四等', '十五等'];

const HUNAN_PAID_LAND_USE_FEE_STANDARDS = {
  一等: '140', 二等: '120', 三等: '100', 四等: '80', 五等: '64',
  六等: '56', 七等: '48', 八等: '42', 九等: '34', 十等: '28',
  十一等: '24', 十二等: '20', 十三等: '16', 十四等: '14', 十五等: '10',
};

const costCompensationZoneOptions = computed(() => {
  const options = costAnalysis.value?.compensation_zone_options || ['Ⅰ', 'Ⅱ', 'Ⅲ'];
  return options.map(zone => `${zone}区`);
});

const paidLandUseFeeStandardByGrade = (gradeName) => {
  const table = {
    ...HUNAN_PAID_LAND_USE_FEE_STANDARDS,
    ...(costAnalysis.value?.paid_land_use_fee_grade_standards || {}),
  };
  const value = table[gradeName];
  return parseCostNumber(value);
};

let costTaxRecalcTimer = null;
const scheduleCostTaxRecalc = () => {
  clearTimeout(costTaxRecalcTimer);
  costTaxRecalcTimer = setTimeout(() => {
    calculateCostApproximation();
  }, 400);
};

const applyWaterConservancyGradeLocally = (item) => {
  if (!item) return;
  const paid = paidLandUseFeeStandardByGrade(item.grade_name);
  item.coefficient = '10';
  if (!Number.isFinite(paid)) {
    item.standard_value = '';
    item.amount_per_sqm = '';
    return;
  }
  item.standard_value = formatCostNumber(paid);
  item.amount_per_sqm = formatCostNumber(paid * 0.1);
};

const costGradeOptions = (item) => {
  if (item?.key === 'land_compensation') return costCompensationZoneOptions.value;
  if (item?.key === 'water_conservancy_fund') return paidLandUseGradeOptions;
  if (item?.key === 'farmland_reclamation_fee') return ['优等水田', '高等水田', '中等水田', '低等水田', '旱地'];
  if (item?.key === 'farmland_occupation_tax') return ['道县适用税额', '其他县市适用税额'];
  return [];
};

const onCostGradeChange = async (item) => {
  if (!item) return;
  item.confirmed = false;
  if (item.key === 'land_compensation') {
      costAnalysis.value.compensation_zone = String(item.grade_name || '').replace('区', '') || costAnalysis.value.compensation_zone;
    costAnalysis.value.compensation_zone_override = true;
    invalidateCostStandardItems(['acquisition_items', 'tax_items']);
    const landItem = (costAnalysis.value?.acquisition_items || []).find(entry => entry.key === 'land_compensation');
    if (landItem) {
      landItem.standard_value = '';
      landItem.amount_per_sqm = '';
    }
    await calculateCostApproximation();
      showToast('已切换征地区片，系统已按新区片价重算。', 'info');
    return;
  }
  if (item.key === 'water_conservancy_fund') {
    applyWaterConservancyGradeLocally(item);
    await calculateCostApproximation();
      showToast('已切换有偿使用费等别，标准值与金额已更新。', 'info');
    return;
  }
  if (item.key === 'farmland_reclamation_fee' || item.key === 'farmland_occupation_tax') {
    await calculateCostApproximation();
    showToast('已切换等别/口径，系统已按新标准重算。', 'info');
    return;
  }
  if (item.rule_key) showToast('已修改政策自动匹配的等别/口径，请同步核对标准值和依据文件。', 'warning');
};

const parseCostNumber = (value) => {
  const text = String(value ?? '').replace(/,/g, '').replace(/％/g, '%').trim();
  const match = text.match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : NaN;
};

const COST_MU_TO_SQM = 0.0015;

const formatCostNumber = (value, digits = 2) => (
  Number.isFinite(value) ? value.toFixed(digits) : ''
);

const costItemLandClassCoefficient = (item) => {
  if (item?.key !== 'land_compensation') return 1;
  const value = parseCostNumber(item.coefficient);
  return Number.isFinite(value) ? value : 1;
};

const costItemUsesLandClassCoefficient = () => false;

const costItemUsesUnitConversion = (item) => (
  ['land_compensation', 'seedling_compensation'].includes(item?.key)
  || String(item?.formula || '').includes('×0.0015')
);

const costItemCoefficientHint = (item) => {
  if (item?.key === 'land_compensation') {
    const coef = costItemLandClassCoefficient(item);
    return `地类${coef}×0.0015 亩→㎡`;
  }
  if (costItemUsesUnitConversion(item)) return '×0.0015 亩→㎡';
  return '';
};

const percentValue = (value) => {
  const number = parseCostNumber(value);
  return Number.isFinite(number) ? number / 100 : NaN;
};

const recalculateCostItemAmount = (item) => {
  if (!item) return;
  const standard = parseCostNumber(item.standard_value);
  const coefficient = parseCostNumber(item.coefficient);
  if (!Number.isFinite(standard)) return;
  if (item.key === 'water_conservancy_fund') {
    const rate = Number.isFinite(coefficient) ? coefficient / 100 : percentValue(item.coefficient);
    if (Number.isFinite(rate)) item.amount_per_sqm = formatCostNumber(standard * rate);
    return;
  }
  if (item.key === 'land_compensation') {
    item.amount_per_sqm = formatCostNumber(standard * costItemLandClassCoefficient(item) * COST_MU_TO_SQM);
    return;
  }
  if (item.key === 'seedling_compensation') {
    item.amount_per_sqm = formatCostNumber(standard * COST_MU_TO_SQM);
    return;
  }
  if (item.key === 'farmland_occupation_tax') {
    item.amount_per_sqm = formatCostNumber(standard * (Number.isFinite(coefficient) ? coefficient : 1));
  }
};

const onCostItemValueInput = (item) => {
  markCostItemEdited(item);
  if (item?.key === 'seedling_compensation') {
    item.source = 'manual_policy_replacement';
  }
  recalculateCostItemAmount(item);
};

const costPopulationPerHa = (item) => {
  if (!item) return '';
  const area = parseCostNumber(item.land_area_ha);
  const population = parseCostNumber(item.population);
  if (!Number.isFinite(area) || area <= 0 || !Number.isFinite(population)) return item.population_per_ha || '';
  const value = formatCostNumber(population / area);
  item.population_per_ha = value;
  return value;
};

const onCostPopulationCaseInput = (item) => {
  if (!item) return;
  item.confirmed = false;
  costPopulationPerHa(item);
  recalculateLocalAttachmentAnalysis();
};

const recalculateBuildingCompensationRow = (item) => {
  if (!item) return;
  const standard = parseCostNumber(item.standard);
  const quantity = parseCostNumber(item.quantity);
  const months = parseCostNumber(item.months);
  const divisor = parseCostNumber(item.divisor);
  if (!Number.isFinite(standard) || !Number.isFinite(quantity)) {
    item.amount = '';
    return;
  }
  const monthFactor = Number.isFinite(months) && months > 0 ? months : 1;
  const divisorValue = Number.isFinite(divisor) && divisor > 0 ? divisor : 1;
  item.amount = formatCostNumber(standard * quantity * monthFactor / divisorValue);
};

const recalculateLocalAttachmentAnalysis = () => {
  const rows = costAnalysis.value?.building_compensation_rows || [];
  rows.forEach(recalculateBuildingCompensationRow);
  const buildingPerPerson = rows
    .map(row => parseCostNumber(row.amount))
    .filter(Number.isFinite)
    .reduce((sum, value) => sum + value, 0);
  const densities = (costAnalysis.value?.resettlement_population_cases || [])
    .map(entry => parseCostNumber(costPopulationPerHa(entry)))
    .filter(value => Number.isFinite(value) && value >= 0);
  const averageDensity = densities.length
    ? densities.reduce((sum, value) => sum + value, 0) / densities.length
    : NaN;
  const greenPerSqm = parseCostNumber(costAnalysis.value?.green_seedling_standard_per_mu) * COST_MU_TO_SQM;
  const buildingPerSqm = Number.isFinite(averageDensity) ? buildingPerPerson * averageDensity / 10000 : 0;
  const attachmentPerSqm = (Number.isFinite(buildingPerSqm) ? buildingPerSqm : 0) + (Number.isFinite(greenPerSqm) ? greenPerSqm : 0);
  costAnalysis.value.attachment_compensation_analysis = {
    ...(costAnalysis.value.attachment_compensation_analysis || {}),
    building_compensation_per_person: formatCostNumber(buildingPerPerson),
    average_population_per_ha: Number.isFinite(averageDensity) ? formatCostNumber(averageDensity) : '',
    building_compensation_per_sqm: formatCostNumber(buildingPerSqm),
    green_seedling_per_sqm: Number.isFinite(greenPerSqm) ? formatCostNumber(greenPerSqm) : '',
    attachment_compensation_per_sqm: formatCostNumber(attachmentPerSqm),
  };
  const buildingItem = (costAnalysis.value?.acquisition_items || []).find(entry => entry.key === 'building_compensation');
  if (buildingItem && buildingItem.source !== 'manual_policy_replacement') {
    buildingItem.standard_value = formatCostNumber(buildingPerPerson);
    buildingItem.standard_unit = '元/人';
    buildingItem.amount_per_sqm = formatCostNumber(buildingPerSqm);
    buildingItem.source_note = Number.isFinite(averageDensity) && averageDensity > 0
      ? '建筑物补偿标准、安置农业人口密度结构化测算'
      : '标准值为表3-1合计（元/人）；元/㎡需先填写表3-2安置人口案例';
  }
  const seedlingItem = (costAnalysis.value?.acquisition_items || []).find(entry => entry.key === 'seedling_compensation');
  if (seedlingItem && seedlingItem.source !== 'manual_policy_replacement') {
    const seedlingPerSqm = Number.isFinite(greenPerSqm) ? formatCostNumber(greenPerSqm) : '';
    seedlingItem.amount_per_sqm = seedlingPerSqm;
    seedlingItem.computed_amount_per_sqm = seedlingPerSqm;
  }
  const groundItem = (costAnalysis.value?.acquisition_items || []).find(entry => entry.key === 'ground_attachment');
  if (groundItem) {
    groundItem.amount_per_sqm = formatCostNumber(attachmentPerSqm);
    groundItem.computed_amount_per_sqm = formatCostNumber(attachmentPerSqm);
  }
};

const costAcquisitionItemAmount = (key) => {
  const item = (costAnalysis.value?.acquisition_items || []).find(entry => entry.key === key);
  if (!item || item.enabled === false) return NaN;
  return parseCostNumber(item.amount_per_sqm);
};

const costAttachmentBuildingAmount = computed(() => {
  const value = costAcquisitionItemAmount('building_compensation');
  return Number.isFinite(value) ? formatCostNumber(value) : '';
});

const costAttachmentSeedlingAmount = computed(() => {
  const value = costAcquisitionItemAmount('seedling_compensation');
  return Number.isFinite(value) ? formatCostNumber(value) : '';
});

const costAttachmentTotalAmount = computed(() => {
  const attachment = parseCostNumber(costAnalysis.value?.attachment_compensation_analysis?.attachment_compensation_per_sqm);
  if (Number.isFinite(attachment)) return formatCostNumber(attachment);
  const building = costAcquisitionItemAmount('building_compensation');
  const seedling = costAcquisitionItemAmount('seedling_compensation');
  if (!Number.isFinite(building) && !Number.isFinite(seedling)) return '';
  return formatCostNumber((Number.isFinite(building) ? building : 0) + (Number.isFinite(seedling) ? seedling : 0));
});

const costLocalAcquisitionTotal = computed(() => {
  const land = costAcquisitionItemAmount('land_compensation');
  const attachment = parseCostNumber(costAttachmentTotalAmount.value);
  if (!Number.isFinite(land) && !Number.isFinite(attachment)) return '';
  return formatCostNumber((Number.isFinite(land) ? land : 0) + (Number.isFinite(attachment) ? attachment : 0));
});

const buildingRowReportNote = (item) => String(item?.note || '').trim();

const costBuildingAddCatalog = computed(() => costAnalysis.value?.building_compensation_add_catalog || []);
const costBuildingAddOpen = ref(false);
const costBuildingAddDraft = ref({ rowKey: '', gradeKey: '' });
const costBuildingAddLoading = ref(false);

const costBuildingExistingRowKeys = computed(() => new Set(
  (costAnalysis.value?.building_compensation_rows || []).map(row => row.key).filter(Boolean)
));

const costBuildingAddAvailable = computed(() => (
  costBuildingAddCatalog.value.filter(entry => !costBuildingExistingRowKeys.value.has(entry.row_key))
));

const ensureBuildingAddCatalog = async () => {
  costBuildingAddLoading.value = true;
  try {
    const payload = buildFlatPayload();
    payload.cost_approx_analysis = JSON.parse(JSON.stringify(costAnalysis.value || {}));
    const basis = await apiJson('/api/cost-basis/applicable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload }),
    });
    if (basis?.building_compensation_add_catalog?.length) {
      costAnalysis.value.building_compensation_add_catalog = basis.building_compensation_add_catalog;
    }
    if (basis.building_compensation_policy_help) {
      costAnalysis.value.building_compensation_policy_help = basis.building_compensation_policy_help;
    }
    if (basis.cost_basis_attachment_inventory?.length) {
      costAnalysis.value.cost_basis_attachment_inventory = basis.cost_basis_attachment_inventory;
    }
    if (basis?.paid_land_use_fee_grade_standards) {
      costAnalysis.value.paid_land_use_fee_grade_standards = basis.paid_land_use_fee_grade_standards;
    }
    if (!costAnalysis.value?.building_compensation_add_catalog?.length) {
      const analysis = await apiJson('/api/cost-approximation/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: payload }),
      });
      if (analysis?.building_compensation_add_catalog?.length) {
        costAnalysis.value.building_compensation_add_catalog = analysis.building_compensation_add_catalog;
      }
      if (analysis?.building_compensation_policy_help) {
        costAnalysis.value.building_compensation_policy_help = analysis.building_compensation_policy_help;
      }
    }
  } catch (error) {
    showToast(`政策目录加载失败：{error.message}`, 'error');
  } finally {
    costBuildingAddLoading.value = false;
  }
};

const openCostBuildingAddDialog = async () => {
  await ensureBuildingAddCatalog();
  if (!costBuildingAddCatalog.value.length) {
    showToast('当前县市暂无结构化政策目录，请确认县市名称后点击「计算并校核」。', 'warning');
    return;
  }
  const available = costBuildingAddAvailable.value;
  const first = available[0] || costBuildingAddCatalog.value[0];
  costBuildingAddDraft.value = {
    rowKey: first?.row_key || '',
    gradeKey: first?.grade_options?.find(option => option.is_default)?.key
      || first?.grade_options?.[0]?.key
      || '',
  };
  costBuildingAddOpen.value = true;
  if (!available.length) {
    showToast('目录项目已全部在表中；下表可查看已收录政策项目。', 'info');
  }
};

const costBuildingAddSelected = computed(() => (
  costBuildingAddCatalog.value.find(entry => entry.row_key === costBuildingAddDraft.value.rowKey) || null
));

const costBuildingAddPreview = (entry) => {
  if (!entry) return { standard: '', note: '' };
  const gradeKey = costBuildingAddDraft.value.rowKey === entry.row_key
    ? costBuildingAddDraft.value.gradeKey
    : ((entry.grade_options || []).find(option => option.is_default) || entry.grade_options?.[0])?.key;
  const option = (entry.grade_options || []).find(item => item.key === gradeKey);
  return {
    standard: String(option?.standard ?? entry.template?.standard ?? ''),
    note: String(option?.note ?? entry.template?.note ?? ''),
  };
};

const confirmCostBuildingAddRow = () => {
  const selected = costBuildingAddSelected.value;
  if (!selected) {
    showToast('请选择补偿项目', 'warning');
    return;
  }
  const existingKeys = new Set((costAnalysis.value?.building_compensation_rows || []).map(row => row.key));
  if (existingKeys.has(selected.row_key)) {
    showToast('该补偿项目已在表中，请直接修改现有行', 'warning');
    return;
  }
  const template = JSON.parse(JSON.stringify(selected.template || {}));
  const option = (selected.grade_options || []).find(entry => entry.key === costBuildingAddDraft.value.gradeKey);
  const row = {
    ...template,
    key: selected.row_key,
    label: template.label || selected.label,
    confirmed: false,
    grade_options: selected.grade_options || [],
    structure_grade: option?.key || template.structure_grade || '',
    standard: String(option?.standard ?? template.standard ?? ''),
    note: String(option?.note ?? template.note ?? ''),
  };
  costAnalysis.value.building_compensation_rows ||= [];
  costAnalysis.value.building_compensation_rows.push(row);
  costBuildingAddOpen.value = false;
  recalculateLocalAttachmentAnalysis();
  showToast(`已添加「${row.label}」`, 'success');
};

const buildingRowStandardReadonly = (item) => {
  if (item?.conversion_check?.status === 'match') return true;
  if (item?.review_status === 'verified' && item?.source_path && item?.key === 'house_compensation') return true;
  return false;
};

const costBuildingPolicyHelp = computed(() => costAnalysis.value?.building_compensation_policy_help || { entries: [] });
const costBuildingPolicyHelpGroups = computed(() => {
  const entries = costBuildingPolicyHelp.value?.entries || [];
  const groups = [];
  const byLabel = new Map();
  for (const entry of entries) {
    const label = entry.row_label || entry.label || '其他';
    let group = byLabel.get(label);
    if (!group) {
      group = { label, rows: [] };
      byLabel.set(label, group);
      groups.push(group);
    }
    group.rows.push(entry);
  }
  return groups;
});
const costBasisAttachmentInventory = computed(() => costAnalysis.value?.cost_basis_attachment_inventory || []);
const costAttachmentStatusLabel = (status) => {
  const labels = {
    verified: '已校核',
    verified_partial: '已结构化校核',
    scan_reference: '扫描件参考',
    scan_pending_structuring: '扫描件待结构化',
    pending_ocr: '待OCR识别',
    conversion_warning: '转换告警，待人工核对',
    available: '已收集',
    missing: '待收集',
  };
  return labels[status] || '待校核';
};
const formatCostAttachmentCounties = (counties) => {
  const list = Array.isArray(counties) ? counties.filter(Boolean) : [];
  if (!list.length) return '-';
  if (list.includes('*')) return '全省';
  const stripSuffix = (name) => String(name).replace(/侗族自治县|苗族自治县|土家族自治县|瑶族自治县|自治县|城区|县|市/g, '');
  const merged = [];
  for (const raw of list) {
    const name = String(raw).trim();
    const key = stripSuffix(name);
    const existing = merged.find(item => item.key === key);
    if (!existing) {
      merged.push({ key, name });
    } else if (name.length < existing.name.length) {
      // Prefer the shorter canonical form (e.g. 通道县over 通道侗族自治县.
      existing.name = name;
    }
  }
    return merged.map(item => item.name).join('、');
};
const costAttachmentCounties = (item) => {
  const display = Array.isArray(item?.counties_display) ? item.counties_display.filter(Boolean) : [];
  if (display.length) {
    if (display.includes('*')) return '全省';
    return display.join('、');
  }
  return formatCostAttachmentCounties(item?.counties);
};
const costAttachmentStatus = (item) => {
  const label = String(item?.status_label || '').trim();
  if (label && label !== item?.status) return label;
  return costAttachmentStatusLabel(item?.status);
};
const costAttachmentStructuredStatus = (item) => {
  const label = String(item?.structured_status_label || '').trim();
  if (label) return label;
  const labels = {
    structured: '已结构化',
    needs_grade_selection: '需选择等别',
    manual_input: '需人工录入',
    reference_only: '说明依据',
    pending_structuring: '待结构化',
  };
  return labels[item?.structured_status] || costAttachmentStatus(item);
};
const costAttachmentStructuredStatusClass = (item) => {
  const status = String(item?.structured_status || '').trim();
  return {
    structured: 'ok',
    needs_grade_selection: 'warning',
    manual_input: 'manual',
    reference_only: 'muted',
    pending_structuring: 'pending',
  }[status] || 'muted';
};
const costAttachmentPriceFields = (item) => {
  const fields = Array.isArray(item?.price_fields) ? item.price_fields.filter(Boolean) : [];
  return fields.filter(field => !String(field).endsWith('.cost_basis_attachment_inventory'));
};
const costAttachmentFieldLabel = (field) => {
  const text = String(field || '');
  if (text.includes('green_seedling_standard_per_mu')) return '青苗标准';
  if (text.includes('building_compensation_rows')) return '建筑物补偿';
  if (text.includes('compensation_zone_suggestion')) return '区片推荐';
  if (text.includes('compensation_zone')) return '征地区片';
  if (text.includes('land_compensation.standard_value')) return '区片价';
  if (text.includes('water_conservancy_fund.grade_name')) return '水利等别';
  if (text.includes('water_conservancy_fund.standard_value')) return '水利标准';
  if (text.includes('farmland_occupation_tax.grade_name')) return '占用税口径';
  if (text.includes('farmland_reclamation_fee.grade_name')) return '开垦费等别';
  if (text.includes('social_security_fund.amount_per_sqm')) return '社保费';
  if (text.includes('forest_restoration_fee.grade_name')) return '森林恢复费';
  return '前往字段';
};

const addCostBuildingCompensationRow = async () => {
  await openCostBuildingAddDialog();
};

const openCostBuildingCompensationHelp = async () => {
  try {
    await ensureBuildingAddCatalog();
    if (!(costAnalysis.value?.building_compensation_policy_help?.entries || []).length) {
      await calculateCostApproximation();
    }
  } catch (error) {
    showToast(`政策标准加载失败：{error.message}`, 'error');
  }
  costBuildingHelpOpen.value = true;
};

const buildLocalPricingControls = (analysisSnapshot = null) => {
  const snapshot = analysisSnapshot || costAnalysis.value || {};
  const controls = [];
  const landItem = (snapshot?.acquisition_items || []).find(item => item.key === 'land_compensation');
  if (landItem?.enabled !== false) {
      const zoneOptions = (snapshot?.compensation_zone_options || ['Ⅰ', 'Ⅱ', 'Ⅲ']).map(zone => String(zone).replace('区', ''));
    controls.push({
      key: 'land_compensation',
      label: '征地区片',
      type: 'grade',
      value: String(landItem?.grade_name || '').replace('区', '') || snapshot?.compensation_zone || '',
      options: zoneOptions,
      amount_per_sqm: landItem?.amount_per_sqm || '',
    });
  }
  for (const row of snapshot?.building_compensation_rows || []) {
    if (!row?.key) continue;
    controls.push({
      key: `building:${row.key}`,
      label: `表3-1 ${row.label || row.key}`,
      type: 'standard',
      value: row.standard || '',
      amount_per_sqm: row.amount || '',
    });
  }
  for (const item of snapshot?.tax_items || []) {
    if (item.enabled === false) continue;
    if (['farmland_occupation_tax', 'social_security_fund'].includes(item.key)) {
      controls.push({
        key: item.key,
        label: item.label,
        type: 'standard',
        value: item.standard_value || item.amount_per_sqm || '',
        amount_per_sqm: item.amount_per_sqm || '',
      });
      continue;
    }
    const gradeOptions = costGradeOptions(item);
    if (gradeOptions.length) {
      controls.push({
        key: item.key,
        label: item.label,
        type: 'grade',
        value: item.grade_name || '',
        options: gradeOptions,
        amount_per_sqm: item.amount_per_sqm || '',
      });
    } else if (item.key !== 'ground_attachment') {
      controls.push({
        key: item.key,
        label: item.label,
        type: 'standard',
        value: item.standard_value || item.amount_per_sqm || '',
        amount_per_sqm: item.amount_per_sqm || '',
      });
    }
  }
  for (const item of snapshot?.acquisition_items || []) {
    if (item.enabled === false || ['land_compensation', 'ground_attachment'].includes(item.key)) continue;
    controls.push({
      key: item.key,
      label: item.label,
      type: 'standard',
      value: item.standard_value || item.amount_per_sqm || '',
      amount_per_sqm: item.amount_per_sqm || '',
    });
  }
  for (const item of snapshot?.development_items || []) {
    if (item.enabled === false) continue;
    controls.push({
      key: `development:${item.label}`,
      label: `开发费·${item.label}`,
      type: 'standard',
      value: item.standard_value || item.amount_per_sqm || '',
      amount_per_sqm: item.amount_per_sqm || '',
    });
  }
  const locationMode = snapshot?.location_correction_mode || 'direct_sum';
  for (const factor of snapshot?.location_factors || []) {
    if (factor.enabled === false) continue;
    if (locationMode === 'direct_sum') {
      controls.push({
        key: `location:${factor.key || factor.label}`,
        label: `区位·${factor.label || factor.key}`,
        type: 'grade',
        value: factor.level || '',
        options: (factor.levels && factor.levels.length) ? factor.levels : ['优', '较优', '一般', '较劣', '劣'],
        amount_per_sqm: factor.correction_rate || '0.00',
      });
    } else {
      controls.push({
        key: `location:${factor.key || factor.label}`,
        label: `区位·${factor.label || factor.key}`,
        type: 'standard',
        value: factor.correction_rate || '0.00',
        amount_per_sqm: factor.correction_rate || '0.00',
      });
    }
  }
  for (const group of snapshot?.risk_groups || []) {
    if (group.enabled === false) continue;
    controls.push({
      key: `risk:${group.key || group.label}`,
      label: `风险·${group.label || group.key}`,
      type: 'standard',
      value: group.override_value || group.effective_value || group.combined_rate || group.rate || '0.00',
      amount_per_sqm: group.effective_value || group.override_value || '0.00',
    });
  }
  return controls;
};

const costPricingSandbox = ref(null);
const costPricingPreview = ref(null);
const costPricingLoading = ref(false);

const costPricingAssistant = computed(() => costPricingPreview.value?.pricing_assistant || costAnalysis.value?.pricing_assistant || {});
const costPricingScenarios = computed(() => {
  const scenarios = costPricingAssistant.value?.scenarios || [];
  if (scenarios.length) return scenarios;
  return [{ key: 'current', label: '当前方案（基线）', final_price: costAnalysis.value?.usage_results?.[0]?.final_price || '', formula_parts: [] }];
});
const costPricingControls = computed(() => {
  const serverControls = costPricingAssistant.value?.controls || [];
  if (serverControls.length) return serverControls;
  return buildLocalPricingControls(costPricingSandbox.value || costAnalysis.value);
});
const costPricingFormulaParts = computed(() => {
  const scenario = costPricingScenarios.value.find(item => item.key === costPricingScenarioKey.value);
  return scenario?.formula_parts || costPricingAssistant.value?.formula_parts || [];
});
const costPricingPreviewFinalPrice = computed(() => {
  const scenario = costPricingScenarios.value.find(item => item.key === costPricingScenarioKey.value);
  return scenario?.final_price
    || costPricingPreview.value?.usage_results?.[0]?.final_price
    || costPricingAssistant.value?.baseline_final_price
    || '';
});
const costPricingPreviewCostPrice = computed(() => {
  const scenario = costPricingScenarios.value.find(item => item.key === costPricingScenarioKey.value);
  return scenario?.cost_price
    || costPricingPreview.value?.usage_results?.[0]?.cost_price
    || costPricingAssistant.value?.baseline_cost_price
    || '';
});
const costPricingChangedItems = computed(() => {
  const scenario = costPricingScenarios.value.find(item => item.key === costPricingScenarioKey.value);
  return scenario?.changed_items || [];
});
const costPricingEntryPoints = computed(() => costPricingAssistant.value?.entry_points || []);

const isCostPricingChanged = (key) => costPricingChangedKeys.value.includes(key);

const recalculateCostPricingSandbox = async () => {
  if (!costPricingSandbox.value) return;
  const payload = buildFlatPayload();
  payload.cost_pricing_preview_mode = true;
  payload.cost_approx_analysis = JSON.parse(JSON.stringify(costPricingSandbox.value));
  const analysis = await apiJson('/api/cost-approximation/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: payload, overwrite: false }),
  });
  costPricingPreview.value = analysis;
  costPricingSandbox.value = JSON.parse(JSON.stringify(analysis || costPricingSandbox.value));
};

const recalculateCostPricingSandboxFromMain = async () => {
  const payload = buildFlatPayload();
  payload.cost_pricing_preview_mode = true;
  payload.cost_approx_analysis = JSON.parse(JSON.stringify(costAnalysis.value || {}));
  const analysis = await apiJson('/api/cost-approximation/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: payload, overwrite: false }),
  });
  costPricingSandbox.value = JSON.parse(JSON.stringify(analysis || costAnalysis.value || {}));
  costPricingPreview.value = JSON.parse(JSON.stringify(costPricingSandbox.value));
};

const applyCostPricingToMain = async () => {
  if (!costPricingSandbox.value) return;
  applyCostAnalysisToForm(costPricingPreview.value || costPricingSandbox.value);
  await loadValuationProcessDraft();
  showToast('调价助手试算结果已应用到主表。', 'success');
};

const openCostPricingAssistant = async () => {
  costPricingAssistantOpen.value = true;
  costPricingLoading.value = true;
  try {
    await flushCostInteractiveCalculation();
    await recalculateCostPricingSandboxFromMain();
    if (!costPricingScenarioKey.value) costPricingScenarioKey.value = 'current';
  } catch (error) {
    showToast(`调价助手加载失败：{error.message}`, 'error');
  } finally {
    costPricingLoading.value = false;
  }
};

const applyCostPricingScenario = async (scenarioKey) => {
  const scenario = costPricingScenarios.value.find(item => item.key === scenarioKey);
  if (!scenario || !costPricingSandbox.value) return;
  costPricingChangedKeys.value = (scenario.changed_items || []).map(item => item.key);
  for (const item of costPricingSandbox.value?.tax_items || []) {
    if (Object.prototype.hasOwnProperty.call(scenario.overrides || {}, item.key)) {
      item.grade_name = scenario.overrides[item.key];
      item.confirmed = false;
    }
  }
  if (scenarioKey === 'current') {
    costPricingChangedKeys.value = [];
  }
  costPricingLoading.value = true;
  try {
    await recalculateCostPricingSandbox();
  } finally {
    costPricingLoading.value = false;
  }
};

const onCostPricingControlChange = async (control, event) => {
  if (!control || !costPricingSandbox.value) return;
  const value = event?.target?.value ?? control.value;
  costPricingScenarioKey.value = 'custom';
  costPricingChangedKeys.value = [control.key];
  const sandbox = costPricingSandbox.value;
  if (String(control.key || '').startsWith('location:')) {
    const factorKey = String(control.key).replace('location:', '');
    const factor = (sandbox?.location_factors || []).find(item => (item.key || item.label) === factorKey);
    if (factor) {
      if (control.type === 'grade') {
        factor.level = value;
        factor.correction_rate_manual = false;
      } else {
        factor.correction_rate = value;
        factor.correction_rate_manual = true;
      }
      factor.confirmed = false;
    }
  } else if (control.type === 'grade' && control.key === 'land_compensation') {
    sandbox.compensation_zone = String(value || '').replace('区', '');
    sandbox.compensation_zone_override = true;
    const landItem = (sandbox?.acquisition_items || []).find(item => item.key === 'land_compensation');
    if (landItem) {
      landItem.grade_name = value ? `${value}区` : '';
      landItem.standard_value = '';
      landItem.amount_per_sqm = '';
      landItem.confirmed = false;
    }
  } else if (control.type === 'grade') {
    const taxItem = (sandbox?.tax_items || []).find(item => item.key === control.key);
    if (taxItem) {
      taxItem.grade_name = value;
      taxItem.confirmed = false;
      if (control.key === 'water_conservancy_fund') {
        const paid = paidLandUseFeeStandardByGrade(value);
        taxItem.coefficient = '10';
        if (Number.isFinite(paid)) {
          taxItem.standard_value = formatCostNumber(paid);
          taxItem.amount_per_sqm = formatCostNumber(paid * 0.1);
        }
      }
    }
  } else if (control.type === 'standard') {
    if (String(control.key || '').startsWith('development:')) {
      const label = String(control.key).replace('development:', '');
      const devItem = (sandbox?.development_items || []).find(item => item.label === label);
      if (devItem) {
        devItem.standard_value = value;
        devItem.amount_per_sqm = value;
        devItem.confirmed = false;
      }
    } else if (String(control.key || '').startsWith('risk:')) {
      const riskKey = String(control.key).replace('risk:', '');
      const group = (sandbox?.risk_groups || []).find(item => item.key === riskKey);
      if (group) {
        group.override_enabled = true;
        group.override_value = value;
        group.effective_value = value;
        group.confirmed = false;
      }
    } else if (String(control.key || '').startsWith('building:')) {
      const rowKey = String(control.key).replace('building:', '');
      const row = (sandbox?.building_compensation_rows || []).find(item => item.key === rowKey);
      if (row) {
        row.standard = value;
        row.confirmed = false;
        recalculateBuildingCompensationRow(row);
      }
    } else {
      const acquisitionItem = (sandbox?.acquisition_items || []).find(item => item.key === control.key);
      if (acquisitionItem) {
        acquisitionItem.standard_value = value;
        if (['building_compensation', 'seedling_compensation'].includes(acquisitionItem.key)) {
          acquisitionItem.amount_per_sqm = value;
          acquisitionItem.source = 'manual_policy_replacement';
        }
        acquisitionItem.confirmed = false;
      } else {
        const taxItem = (sandbox?.tax_items || []).find(item => item.key === control.key);
        if (taxItem) {
          taxItem.standard_value = value;
          taxItem.amount_per_sqm = value;
          taxItem.confirmed = false;
        }
      }
    }
  }
  costPricingLoading.value = true;
  try {
    await recalculateCostPricingSandbox();
  } catch (error) {
    showToast(`试算失败：${error.message}`, 'error');
  } finally {
    costPricingLoading.value = false;
  }
};

const openCostPricingEntryPoint = (entry) => {
  costPricingAssistantOpen.value = false;
  if (entry?.workspace) costWorkspaceView.value = entry.workspace;
  activeTab.value = 'p5';
  if (entry?.section_id) {
    nextTick(() => {
      const el = document.getElementById(entry.section_id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
};

const onBuildingCompensationGradeChange = (item) => {
  if (!item) return;
  const option = (item.grade_options || []).find(entry => entry.key === item.structure_grade);
  if (!option) {
    onBuildingCompensationRowInput(item);
    return;
  }
  item.standard = String(option.standard ?? item.standard ?? '');
  if (option.note) item.note = option.note;
  item.confirmed = false;
  recalculateLocalAttachmentAnalysis();
};

const onBuildingCompensationRowInput = (item) => {
  if (!item) return;
  item.confirmed = false;
  recalculateLocalAttachmentAnalysis();
};

const costBuildingPopulationMissing = computed(() => {
  const perPerson = parseCostNumber(costAnalysis.value?.attachment_compensation_analysis?.building_compensation_per_person);
  if (!Number.isFinite(perPerson) || perPerson <= 0) return false;
  const densities = (costAnalysis.value?.resettlement_population_cases || [])
    .map(item => parseCostNumber(costPopulationPerHa(item)))
    .filter(value => Number.isFinite(value) && value > 0);
  return densities.length === 0;
});

const normalizeCostZoneLabel = (value) => String(value || '').trim().replace('区', '');

const costZoneSuggestionAvailable = computed(() => Boolean(
  costAnalysis.value?.compensation_zone_suggestion?.matched
  && costAnalysis.value?.compensation_zone_suggestion?.compensation_zone
));

const costZoneSuggestionSummary = computed(() => {
  const suggestion = costAnalysis.value?.compensation_zone_suggestion || {};
  if (suggestion.matched) {
    const confidenceMap = {
      village: '村/社区级',
      township: '乡镇级',
      town: '镇级',
      street: '街道级',
      township_partial: '乡镇部分',
      approximate: '近似匹配',
    };
    const confidence = confidenceMap[suggestion.confidence] || suggestion.confidence || '';
    const detail = suggestion.match_detail || suggestion.scope_text || '';
    return `推荐 ${suggestion.compensation_zone}区${detail ? ` · ${detail}` : ''}${confidence ? `（${confidence}）` : ''}`;
  }
  return (suggestion.warnings || []).join('；') || '';
});

const costPopulationAverage = computed(() => {
  const values = (costAnalysis.value?.resettlement_population_cases || [])
    .map(item => parseCostNumber(costPopulationPerHa(item)))
    .filter(value => Number.isFinite(value));
  if (!values.length) return costAnalysis.value?.attachment_compensation_analysis?.average_population_per_ha || '';
  return formatCostNumber(values.reduce((sum, value) => sum + value, 0) / values.length);
});

const costLocationTemplateOptions = [
  { key: 'residential_general', label: '住宅通用' },
  { key: 'commercial_fuel_station', label: '商服加油站' },
  { key: 'custom', label: '自定义' }
];

const costItemUsesCoefficient = (item) => {
  const formula = String(item?.formula || '');
  if (costItemUsesLandClassCoefficient(item)) return false;
  if (['farmland_occupation_tax', 'seedling_compensation'].includes(item?.key)) return false;
  if (costItemUsesUnitConversion(item)) return false;
  return item?.key === 'water_conservancy_fund' || Boolean(item?.coefficient) || formula.includes('系数');
};

const costItemAmountReadonly = (item) => [
  'land_compensation',
  'building_compensation',
  'seedling_compensation',
  'water_conservancy_fund',
  'farmland_occupation_tax',
  'farmland_reclamation_fee',
  'forest_restoration_fee'
].includes(item?.key) || ['structured_attachment_analysis', 'not_applicable'].includes(item?.source);

const costItemSourceReadonly = (item) => ['policy_config', 'structured_attachment_analysis', 'not_applicable', 'compat_derived'].includes(item?.source);

const markCostItemEdited = (item) => {
  if (item) item.confirmed = false;
};

const onCostItemEnabledChange = (item) => {
  if (!item) return;
  item.confirmed = false;
  if (item.enabled === false && item.key !== 'ground_attachment') {
    item.amount_per_sqm = '0.00';
  }
};

const costItemStandardPlaceholder = (item) => {
  if (item?.key === 'land_compensation') {
    const zone = normalizeCostZoneLabel(costAnalysis.value?.compensation_zone);
    if (zone === 'III' || zone === 'Ⅲ') return 'III区未配置区片价';
    return '待匹配区片价';
  }
  if (item?.source === 'external_result') return '外部结果';
  return '标准值';
};

const costLandCompensationZoneHint = computed(() => {
  const zone = normalizeCostZoneLabel(costAnalysis.value?.compensation_zone);
  if (zone !== 'III' && zone !== 'Ⅲ') return '';
  return '湖南省征地补偿标准表中道县未配置 III 区片价，请改用 I/II 区或人工填写标准值。';
});

const invalidateCostStandardItems = (groups = ['acquisition_items', 'tax_items', 'development_items']) => {
  groups.forEach(key => {
    (costAnalysis.value?.[key] || []).forEach(item => {
      if (item.source !== 'external_result') item.confirmed = false;
    });
  });
  (costAnalysis.value?.policy_documents || []).forEach(item => {
    if (item.source_type === 'system_recommendation') item.confirmed = false;
  });
};

const invalidateCostLandClassDependents = () => {
  invalidateCostStandardItems(['acquisition_items', 'tax_items']);
  form.acquisition_land_class_confirmed.value = true;
};

const onCostCompensationZoneChange = async () => {
  const suggested = normalizeCostZoneLabel(costAnalysis.value?.compensation_zone_suggestion?.compensation_zone);
  const current = normalizeCostZoneLabel(costAnalysis.value?.compensation_zone);
  costAnalysis.value.compensation_zone_override = Boolean(suggested && current && suggested !== current);
  invalidateCostStandardItems(['acquisition_items', 'tax_items', 'development_items']);
  await calculateCostApproximation();
};

const applyCostZoneSuggestion = async () => {
  const zone = costAnalysis.value?.compensation_zone_suggestion?.compensation_zone;
  if (!zone) {
    showToast('当前没有可用的区片推荐，请填写位置全称后重新匹配。', 'warning');
    return;
  }
  costAnalysis.value.compensation_zone = zone;
  costAnalysis.value.compensation_zone_override = false;
  invalidateCostStandardItems(['acquisition_items', 'tax_items', 'development_items']);
  await calculateCostApproximation();
};

let costZoneRematchTimer = null;
const scheduleCostZoneRematch = () => {
  if (!form.use_cost_approx.value || costAnalysis.value?.compensation_zone_override) return;
  clearTimeout(costZoneRematchTimer);
  costZoneRematchTimer = setTimeout(() => {
    if (!String(form.land_location_full.value || form.land_location.value || '').trim()) return;
    rematchCostApproximation();
  }, 800);
};

const onCostRiskModeChange = async () => {
  (costAnalysis.value?.usage_scenarios || []).forEach(item => { item.confirmed = false; });
  await calculateCostApproximation();
};

const onCostLocationTemplateChange = async () => {
  costAnalysis.value.location_factors = [];
  await calculateCostApproximation();
};

const costRiskLevelOptions = (item) => item?.level_options?.length
  ? item.level_options
  : [
      { level: 'D', adjustment_rate: '0' },
      { level: 'C', adjustment_rate: '2' },
      { level: 'B', adjustment_rate: '4' },
      { level: 'A', adjustment_rate: '8' }
    ];

const onCostRiskLevelChange = (item) => {
  const match = costRiskLevelOptions(item).find(option => option.level === item.level);
  if (match) item.adjustment_rate = match.adjustment_rate;
  item.confirmed = false;
  (costAnalysis.value?.risk_groups || []).forEach(group => { group.confirmed = false; });
};

const costLocationLevels = (factor) => factor?.levels?.length
  ? factor.levels
  : ['优', '较优', '一般', '较劣', '劣'];

const computeLocationCorrectionRate = (factor) => {
  const amplitude = parseFloat(factor?.grade_amplitude) || 0;
  const levels = (factor?.levels && factor.levels.length) ? factor.levels.map(String) : ['优', '较优', '一般', '较劣', '劣'];
  const level = String(factor?.level || '').trim();
  if (level && levels.includes(level)) {
    const center = (levels.length - 1) / 2;
    return amplitude * (center - levels.indexOf(level));
  }
  const multiplier = { '优': 2, '较优': 1, '一般': 0, '较劣': -1, '劣': -2 }[level] || 0;
  return amplitude * multiplier;
};

const recalculateLocalLocationResults = () => {
  const analysis = costAnalysis.value || {};
  const factors = analysis.location_factors || [];
  const scenarios = analysis.usage_scenarios || [];
  const results = analysis.usage_results || [];
  scenarios.forEach((scenario) => {
    const total = factors
      .filter(item => item?.enabled !== false && (!item.usage_key || item.usage_key === scenario.key))
      .reduce((sum, item) => {
        const rate = parseCostNumber(item.correction_rate);
        return sum + (Number.isFinite(rate) ? rate : 0);
      }, 0);
    scenario.location_correction_rate = formatCostNumber(total);
    const usageResult = results.find(item => item.key === scenario.key);
    if (!usageResult) return;
    usageResult.location_correction_rate = formatCostNumber(total);
    const comparablePrice = parseCostNumber(usageResult.comparable_price);
    if (Number.isFinite(comparablePrice)) {
      usageResult.final_price = formatCostNumber(comparablePrice * (1 + total / 100), 1);
    }
  });
  if (results.length === 1 && results[0]?.final_price) {
    analysis.cost_approx_price = results[0].final_price;
    form.cost_approx_price.value = results[0].final_price;
    form.cost_approx_price.origin = 'generated';
    form.cost_approx_price.is_dirty = false;
  }
};

const onCostLocationFactorChanged = (factor, manualRate = false) => {
  if (!factor) return;
  if (manualRate) factor.correction_rate_manual = true;
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const onCostLocationAmplitudeInput = (factor) => {
  if (!factor) return;
  if ((costAnalysis.value?.location_correction_mode) === 'direct_sum') {
    factor.correction_rate = formatCostNumber(computeLocationCorrectionRate(factor));
    factor.correction_rate_manual = false;
  }
  factor.confirmed = false;
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const onCostLocationLevelChange = (factor) => {
  if (!factor) return;
  if ((costAnalysis.value?.location_correction_mode) === 'direct_sum') {
    factor.correction_rate = formatCostNumber(computeLocationCorrectionRate(factor));
    factor.correction_rate_manual = false;
  }
  factor.confirmed = false;
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const queryLatestLpr = async () => {
  try {
    latestLpr.value = await apiJson('/api/cost-approximation/lpr');
    showToast(`已获取LPR：${latestLpr.value.date}，1年期${latestLpr.value.one_year}%`, 'success');
  } catch (error) {
    showToast(`LPR查询失败：{error.message}`, 'error');
  }
};

const applyLatestLpr = () => {
  if (!latestLpr.value?.one_year) return;
  costAnalysis.value.interest_rate = latestLpr.value.one_year;
  (costAnalysis.value?.usage_scenarios || []).forEach(item => { item.confirmed = false; });
  showToast('已将最新1年期LPR写入投资利息率，请重新计算确认。', 'success');
};

const rematchCostApproximation = async () => {
  invalidateCostStandardItems(['acquisition_items', 'tax_items', 'development_items']);
  await calculateCostApproximation();
};

const onAcquisitionLandClassChange = async () => {
  const options = acquisitionLandSubclassOptions.value;
  if (!options.includes(form.acquisition_land_subclass.value)) {
    form.acquisition_land_subclass.value = options[0] || '水田';
  }
  invalidateCostLandClassDependents();
  await calculateCostApproximation();
};

const onAcquisitionLandSubclassChange = async () => {
  const matched = Object.entries(acquisitionLandClassTree).find(([, items]) => items.includes(form.acquisition_land_subclass.value));
  if (matched) form.acquisition_land_class.value = matched[0];
  invalidateCostLandClassDependents();
  await calculateCostApproximation();
};

const applyCostAnalysisToForm = (analysis) => {
  costAnalysis.value = JSON.parse(JSON.stringify(analysis || {}));
  syncCostAnalysisSnapshotToForm();
  recalculateLocalAttachmentAnalysis();
  if (analysis?.effective_local_city && !form.local_city.is_dirty) {
    form.local_city.value = analysis.effective_local_city;
    form.local_city.origin = 'generated';
  }
  if (analysis?.cost_approx_price) {
    form.cost_approx_price.value = analysis.cost_approx_price;
    form.cost_approx_price.origin = 'generated';
    form.cost_approx_price.is_dirty = false;
  }
  ['local_compensation_policy_name', 'local_compensation_policy_no', 'local_compensation_policy_date'].forEach(key => {
    if (analysis?.[key] && !form[key].is_dirty) {
      form[key].value = analysis[key];
      form[key].origin = 'generated';
    }
  });
  if (analysis?.acquisition_land_class) form.acquisition_land_class.value = analysis.acquisition_land_class;
  if (analysis?.acquisition_land_subclass) form.acquisition_land_subclass.value = analysis.acquisition_land_subclass;
  form.acquisition_land_class_confirmed.value = analysis?.acquisition_land_class_confirmed !== false;
};

const syncCostAnalysisSnapshotToForm = () => {
  form.cost_approx_analysis.value = JSON.parse(JSON.stringify(costAnalysis.value || {}));
  form.cost_approx_analysis.origin = 'generated';
  form.cost_approx_analysis.is_dirty = false;
};

const calculateCostApproximation = async () => {
  if (costRecalcTimer) { clearTimeout(costRecalcTimer); costRecalcTimer = null; }
  cancelCostInteractiveRequest();
  costInteractiveDirty.value = false;
  try {
    const payload = buildFlatPayload();
    const analysis = await apiJson('/api/cost-approximation/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload, overwrite: false })
    });
    applyCostAnalysisToForm(analysis);
    await loadValuationProcessDraft();
    costProcessDraftDirty.value = false;
    showToast(analysis.complete ? '成本逼近法测算已完成并通过确认。' : '成本逼近法已试算，仍有项目待确认。', analysis.complete ? 'success' : 'warning');
  } catch (error) {
    showToast(`成本逼近法计算失败：${error.message}`, 'error');
  }
};

// i3：交互期（如优劣度切换）使用防抖静默重算，不重建正文草稿；
// 正文草稿仅在“计算并校核”按钮或离开第五部分页签时重建。
let costRecalcTimer = null;
const costInteractiveDirty = ref(false);
const costProcessDraftDirty = ref(false);
let costInteractiveRequestSeq = 0;
let costInteractiveAbortController = null;
let costInteractivePromise = null;

const cancelCostInteractiveRequest = () => {
  costInteractiveRequestSeq += 1;
  if (costInteractiveAbortController) costInteractiveAbortController.abort();
  costInteractiveAbortController = null;
  costInteractivePromise = null;
};

const mergeCostArrayByKey = (target, source) => {
  if (!Array.isArray(target) || !Array.isArray(source)) return;
  source.forEach((sourceItem, index) => {
    const key = String(sourceItem?.key || '');
    const targetItem = (key && target.find(item => String(item?.key || '') === key)) || target[index];
    if (targetItem) Object.assign(targetItem, sourceItem);
  });
};

const applyCostInteractiveAnalysis = (analysis) => {
  if (!analysis) return;
  ['usage_scenarios', 'usage_results', 'location_factors', 'risk_items', 'risk_groups'].forEach((key) => {
    mergeCostArrayByKey(costAnalysis.value?.[key], analysis[key]);
  });
  ['totals', 'rounding_trace', 'warnings', 'complete', 'cost_approx_price'].forEach((key) => {
    if (analysis[key] !== undefined) costAnalysis.value[key] = analysis[key];
  });
  if (analysis.cost_approx_price) {
    form.cost_approx_price.value = analysis.cost_approx_price;
    form.cost_approx_price.origin = 'generated';
    form.cost_approx_price.is_dirty = false;
  }
  syncCostAnalysisSnapshotToForm();
};

const calculateCostApproximationSilent = async () => {
  const requestSeq = ++costInteractiveRequestSeq;
  if (costInteractiveAbortController) costInteractiveAbortController.abort();
  const controller = new AbortController();
  costInteractiveAbortController = controller;
  costInteractiveDirty.value = false;
  const request = (async () => {
    const payload = buildFlatPayload();
    payload.cost_interactive_mode = true;
    payload.cost_pricing_preview_mode = true;
    const analysis = await apiJson('/api/cost-approximation/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload, overwrite: false }),
      signal: controller.signal,
    });
    if (requestSeq !== costInteractiveRequestSeq || controller.signal.aborted) return;
    applyCostInteractiveAnalysis(analysis);
  })();
  costInteractivePromise = request;
  try {
    await request;
  } catch (error) {
    if (controller.signal.aborted) return;
    showToast(`成本逼近法计算失败：${error.message}`, 'error');
  } finally {
    if (requestSeq === costInteractiveRequestSeq) {
      costInteractiveAbortController = null;
      costInteractivePromise = null;
    }
  }
};

const scheduleCostInteractiveRecalc = (delay = 450) => {
  costInteractiveDirty.value = true;
  costProcessDraftDirty.value = true;
  if (costRecalcTimer) clearTimeout(costRecalcTimer);
  costRecalcTimer = setTimeout(() => {
    costRecalcTimer = null;
    calculateCostApproximationSilent();
  }, delay);
};

const flushCostInteractiveCalculation = async () => {
  if (costRecalcTimer) { clearTimeout(costRecalcTimer); costRecalcTimer = null; }
  if (costInteractiveDirty.value) {
    await calculateCostApproximationSilent();
  } else if (costInteractivePromise) {
    await costInteractivePromise;
  }
  if (costInteractiveDirty.value) await calculateCostApproximationSilent();
};

const flushCostInteractiveRecalc = async () => {
  await flushCostInteractiveCalculation();
  if (costProcessDraftDirty.value) {
    await loadValuationProcessDraft();
    costProcessDraftDirty.value = false;
  }
};

watch(activeTab, (newTab, oldTab) => {
  if (oldTab === 'p5' && newTab !== 'p5') {
    flushCostInteractiveRecalc();
    flushBenchmarkRecalc();
  }
});

const sourceKeyFragment = (key) => String(key || '').replace(/[^A-Za-z0-9_]+/g, '_');
const incomeSourceKey = (path) => {
  const text = String(path || '');
  return text.startsWith('income_cap_analysis.') ? text : `income_cap_analysis.${text}`;
};
const costSourceKey = (path) => {
  const text = String(path || '');
  return text.startsWith('cost_approx_analysis.') ? text : `cost_approx_analysis.${text}`;
};
const marketSourceKey = (path) => {
  const text = String(path || '');
  return text.startsWith('market_comp_analysis.') ? text : `market_comp_analysis.${text}`;
};
const incomeFocusId = (path) => `focus_item_${sourceKeyFragment(incomeSourceKey(path))}`;
const incomeFocusClass = (path) => ({
  'flicker-glow-active': activeFlickerField.value === incomeSourceKey(path)
});
const costFocusId = (path) => `focus_item_${sourceKeyFragment(costSourceKey(path))}`;
const costFocusClass = (path) => ({
  'flicker-glow-active': activeFlickerField.value === costSourceKey(path)
});
const marketFocusId = (path) => `focus_item_${sourceKeyFragment(marketSourceKey(path))}`;
const marketFocusClass = (path) => ({
  'flicker-glow-active': activeFlickerField.value === marketSourceKey(path)
});
const benchmarkSourceKey = (path) => {
  const text = String(path || '');
  return text.startsWith('benchmark_corr_analysis.') ? text : `benchmark_corr_analysis.${text}`;
};
const benchmarkFocusId = (path) => `focus_item_${sourceKeyFragment(benchmarkSourceKey(path))}`;
const benchmarkFocusClass = (path) => ({
  'flicker-glow-active': activeFlickerField.value === benchmarkSourceKey(path)
});
const numericValue = (value) => {
  const match = String(value ?? '').match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : NaN;
};
const formatLinkedNumber = (value, digits = 2) => {
  if (!Number.isFinite(value)) return '';
  const fixed = value.toFixed(digits);
  return fixed.replace(/\.?0+$/, '');
};
const derivedUseCondition = () => (
  form.valuation_condition_type.value === '规划'
    ? '规划利用条件'
    : form.valuation_condition_type.value === '现状'
      ? '现状使用条件'
      : (form.valuation_condition_type.value ? `${form.valuation_condition_type.value}利用条件` : '')
);
const syncIncomeUseCondition = () => {
  incomeAnalysis.value.building_profile ||= {};
  const profile = incomeAnalysis.value.building_profile;
  profile.current_use_condition = derivedUseCondition();
  profile.current_use_condition_manual = false;
};
const syncIncomePlotRatio = () => {
  incomeAnalysis.value.building_profile ||= {};
  const profile = incomeAnalysis.value.building_profile;
  if (!profile.building_area && form.building_area.value) profile.building_area = form.building_area.value;
  if (!profile.land_area && form.land_area.value) profile.land_area = form.land_area.value;
  const ratio = String(form.set_plot_ratio_display?.value || form.set_plot_ratio?.value || '').trim();
  profile.plot_ratio = ratio;
  profile.set_plot_ratio = ratio;
};
const syncIncomeBuildingYears = (changedKey = '') => {
  incomeAnalysis.value.building_profile ||= {};
  const profile = incomeAnalysis.value.building_profile;
  const life = numericValue(profile.economic_life_years);
  const used = numericValue(profile.used_years);
  const remaining = numericValue(profile.remaining_years);
  const valuationYear = parseCnDate(form.valuation_date.value)?.year;
  const builtYear = numericValue(profile.built_year);
  if (changedKey === 'built_year' && Number.isFinite(valuationYear) && Number.isFinite(builtYear)) {
    profile.used_years = String(Math.max(valuationYear - builtYear, 0));
  }
  if (changedKey === 'remaining_years' && Number.isFinite(life) && Number.isFinite(remaining)) {
    profile.used_years = formatLinkedNumber(Math.max(life - remaining, 0), 1);
  } else if (Number.isFinite(life) && Number.isFinite(numericValue(profile.used_years))) {
    profile.remaining_years = formatLinkedNumber(Math.max(life - numericValue(profile.used_years), 0), 1);
  } else if (!String(profile.used_years || '').trim() && Number.isFinite(valuationYear) && Number.isFinite(builtYear)) {
    profile.used_years = String(Math.max(valuationYear - builtYear, 0));
  }
};
const syncIncomeDerivedFields = (force = false) => {
  incomeAnalysis.value.building_profile ||= {};
  syncIncomeUseCondition();
  syncIncomePlotRatio(force);
};

const setIncomeBasisReference = (key, value, mode = 'replace') => {
  incomeAnalysis.value.building_profile ||= {};
  const selected = String(value || '').trim();
  if (!selected) return;
  const current = String(incomeAnalysis.value.building_profile[key] || '').trim();
  incomeAnalysis.value.building_profile[key] = mode === 'append' && current && !current.includes(selected)
    ? `${current}；${selected}`
    : selected;
};
const inferRentalUsageKey = (value) => {
  const text = String(value || '').trim();
  if (!text) return 'residential';
  if (rentalUsageByKey[text]) return text;
  if (/住宅|居住|公寓/.test(text)) return 'residential';
  if (/商业|商服|商铺|门面|零售/.test(text)) return 'commercial';
  if (/办公|写字楼/.test(text)) return 'office';
  if (/工业|厂房|工矿/.test(text)) return 'industrial';
  if (/仓储|仓库|物流/.test(text)) return 'warehouse';
  return 'other';
};
const onRentUsageChange = (item) => {
  if (!item) return;
  const option = rentalUsageByKey[item.usage_key];
  item.usage = item.usage_key === 'other'
    ? String(item.usage_other || item.usage || '').trim()
    : (option?.label || '');
  syncRentInstanceFactor(item, 'usage');
};
const normalizedIncomeMonth = (value) => {
  const parsed = parseCnDate(value);
  if (parsed?.year && parsed?.month) return `${parsed.year}.${String(parsed.month).padStart(2, '0')}`;
  return String(value || '').trim();
};
const normalizeIncomeFactorValue = (key, value) => {
  const text = String(value || '').trim();
  if (!text) return '';
  if (key === 'usage') {
    const usageKey = inferRentalUsageKey(text);
    return usageKey === 'other' ? text : (rentalUsageByKey[usageKey]?.label || text);
  }
  if (key === 'transaction_time') return normalizedIncomeMonth(text);
  if (key === 'transaction_condition') {
    if (['正常', '正常交易', '正常市场交易'].includes(text)) return '正常交易';
    if (/非正常|异常|关联交易|特殊交易/.test(text)) return '非正常交易';
  }
  const normalized = incomeFactorValueAliases[text] || text;
  const scale = incomeRentFactorScales[key];
  if (!scale?.values?.length) return normalized;
  if (scale.values.includes(normalized)) return normalized;
  const genericIndex = genericIncomeFactorLevels.indexOf(normalized);
  if (scale.scaleType === 'ordered' && genericIndex >= 0) {
    const targetIndex = Math.round(genericIndex * (scale.values.length - 1) / (genericIncomeFactorLevels.length - 1));
    return scale.values[targetIndex];
  }
  return normalized;
};
const buildIncomeFactorLevels = (factor, subjectValue) => {
  const scale = incomeRentFactorScales[factor?.key];
  if (!scale?.values?.length) return [];
  const subjectIndex = scale.values.indexOf(subjectValue);
  return scale.values.map((value, index) => ({
    label: value,
    value,
    quality_score: scale.values.length - index,
    index: subjectIndex >= 0 ? (100 + (subjectIndex - index) * Number(scale.step || 0)).toFixed(2) : '',
    description: `条件为{value}`
  }));
};
const incomeFactorByKey = (key) => (incomeAnalysis.value?.rent_factor_items || []).find(item => item.key === key);
const recalculateIncomeFactorCase = (factor, slot) => {
  const caseItem = factor?.cases?.[slot];
  if (!caseItem) return;
  factor.subject_index = '100.00';
  const subjectValue = normalizeIncomeFactorValue(factor.key, factor.subject_level_label || factor.subject_value);
  const caseValue = normalizeIncomeFactorValue(factor.key, caseItem.level_label || caseItem.value);
  if (factor.scale_type === 'equality_month') {
    caseItem.index = normalizedIncomeMonth(subjectValue) === normalizedIncomeMonth(caseValue) && caseValue ? '100.00' : '';
  } else if (factor.scale_type === 'equality') {
    caseItem.index = subjectValue === caseValue && caseValue ? '100.00' : '';
  } else {
    const subjectLevel = (factor.levels || []).find(level => normalizeIncomeFactorValue(factor.key, level.value || level.label) === subjectValue);
    const caseLevel = (factor.levels || []).find(level => normalizeIncomeFactorValue(factor.key, level.value || level.label) === caseValue);
    const step = numericValue(factor.step) || ({ road_type: 1, ventilation_lighting: 1, internal_layout: 1 }[factor.key] || (factor.key === 'newness' ? 4 : 2));
    if (subjectLevel && caseLevel) {
      caseItem.index = (100 + (Number(caseLevel.quality_score) - Number(subjectLevel.quality_score)) * step).toFixed(2);
    } else {
      caseItem.index = '';
    }
  }
  caseItem.confirmed = false;
};
const normalizeIncomeFactorStandards = () => {
  (incomeAnalysis.value?.rent_factor_items || []).forEach(factor => {
    const scale = incomeRentFactorScales[factor.key];
    if (!scale) return;
    const previousScaleType = factor.scale_type;
    const previousLevelValues = (factor.levels || []).map(level => String(level.value || level.label || '').trim());
    const scaleChanged = previousScaleType !== scale.scaleType
      || previousLevelValues.length !== scale.values.length
      || previousLevelValues.some((value, index) => normalizeIncomeFactorValue(factor.key, value) !== scale.values[index]);
    factor.cases ||= {};
    factor.scale_type = scale.scaleType;
    factor.step = String(scale.step);
    const previousSubjectValue = String(factor.subject_level_label || factor.subject_value || '').trim();
    let subjectValue = normalizeIncomeFactorValue(factor.key, previousSubjectValue);
    if (scale.values.length && !scale.values.includes(subjectValue)) {
      subjectValue = scale.defaultValue || scale.values[Math.floor(scale.values.length / 2)];
    }
    if (subjectValue) {
      factor.subject_value = subjectValue;
      factor.subject_level_label = subjectValue;
    }
    factor.subject_index = '100.00';
    factor.levels = buildIncomeFactorLevels(factor, subjectValue);
    comparableSlots.forEach(slot => {
      factor.cases[slot] ||= { value: '', level_label: '', index: '', source: 'manual', confirmed: false };
      const caseItem = factor.cases[slot];
      const wasConfirmed = Boolean(caseItem.confirmed);
      const previousIndex = String(caseItem.index || '');
      let previousValue = String(caseItem.level_label || caseItem.value || '').trim();
      if (factor.key === 'transaction_condition' && !previousValue) {
        previousValue = '正常交易';
        caseItem.source = 'system_default';
      }
      const normalizedValue = normalizeIncomeFactorValue(factor.key, previousValue);
      let caseChanged = scaleChanged || previousSubjectValue !== subjectValue;
      if (factor.key === 'usage' && normalizedValue) {
        caseChanged ||= previousValue !== normalizedValue;
        caseItem.value = normalizedValue;
        caseItem.level_label = normalizedValue;
      } else if (scale.values.includes(normalizedValue)) {
        caseChanged ||= previousValue !== normalizedValue;
        caseItem.value = normalizedValue;
        caseItem.level_label = normalizedValue;
      } else if (scale.scaleType === 'ordered') {
        caseChanged ||= Boolean(previousValue || previousIndex);
        caseItem.level_label = '';
        caseItem.index = '';
      }
      if (factor.key === 'transaction_condition') {
        caseItem.source = normalizedValue === '正常交易' ? 'system_default' : 'manual_override';
      }
      recalculateIncomeFactorCase(factor, slot);
      if (!caseChanged && previousIndex === String(caseItem.index || '')) {
        caseItem.confirmed = wasConfirmed;
      }
    });
  });
};
const syncRentInstanceFactor = (item, key) => {
  const factor = incomeFactorByKey(key);
  const caseItem = factor?.cases?.[item?.slot];
  if (!factor || !caseItem || caseItem.source === 'manual_override') return;
  caseItem.value = key === 'transaction_time' ? normalizedIncomeMonth(item.transaction_date) : String(item.usage || '').trim();
  caseItem.level_label = caseItem.value;
  caseItem.source = 'rent_instance';
  recalculateIncomeFactorCase(factor, item.slot);
};
const onRentTransactionDateChange = (item) => syncRentInstanceFactor(item, 'transaction_time');
const restoreIncomeFactorInstanceReference = (factor, slot) => {
  const instance = (incomeAnalysis.value?.rent_instances || []).find(item => item.slot === slot);
  if (!instance || !factor?.cases?.[slot] || !['usage', 'transaction_time'].includes(factor.key)) return;
  factor.cases[slot].source = 'rent_instance';
  syncRentInstanceFactor(instance, factor.key);
};
const markIncomeFactorCaseEdited = (factor, slot) => {
  const caseItem = factor?.cases?.[slot];
  if (!caseItem) return;
  caseItem.source = 'manual_override';
  const matching = (factor.levels || []).find(level => level.value === caseItem.value || level.label === caseItem.value);
  caseItem.level_label = matching?.label || '';
  recalculateIncomeFactorCase(factor, slot);
};
const inferIncomeCostStructureKey = (value) => {
  const text = String(value || '').trim();
  if (['steel_concrete', 'brick_concrete', 'brick_wood', 'simple'].includes(text)) return text;
  if (/简易/.test(text)) return 'simple';
  if (/砖木/.test(text)) return 'brick_wood';
  if (/钢混|钢筋混凝土|框架|混凝土/.test(text)) return 'steel_concrete';
  return 'brick_concrete';
};
const defaultIncomeCostGradeKey = (structureKey) => {
  if (structureKey === 'steel_concrete') {
    const floors = numericValue(incomeAnalysis.value?.building_profile?.floor_desc);
    if (Number.isFinite(floors)) {
      if (floors >= 34) return '1';
      if (floors >= 18) return '2';
      if (floors >= 8) return '3';
    }
    return '4';
  }
  if (structureKey === 'brick_concrete') return '1';
  return '';
};
const incomeCostStandardKeyFromParts = (structureKey, gradeKey) => {
  if (structureKey === 'steel_concrete') return `steel_concrete_${gradeKey || '4'}`;
  if (structureKey === 'brick_concrete') return `brick_concrete_${gradeKey || '1'}`;
  if (structureKey === 'brick_wood') return 'brick_wood';
  if (structureKey === 'simple') return 'simple';
  return 'brick_concrete_1';
};
const incomeCostGradeOptions = computed(() => {
  const structureKey = incomeAnalysis.value?.expense_parameters?.replacement_cost_structure_key
    || inferIncomeCostStructureKey(incomeAnalysis.value?.building_profile?.structure);
  return residentialConstructionCostStandards.filter(item => item.structureKey === structureKey);
});
const selectedIncomeCostStandard = computed(() => {
  const expense = incomeAnalysis.value?.expense_parameters || {};
  return residentialConstructionCostByKey[expense.replacement_cost_standard_key]
    || residentialConstructionCostByKey[incomeCostStandardKeyFromParts(expense.replacement_cost_structure_key, expense.replacement_cost_grade_key)]
    || residentialConstructionCostByKey.brick_concrete_1;
});
const syncIncomeCostStandard = (resetAdopted = false) => {
  incomeAnalysis.value.building_profile ||= {};
  incomeAnalysis.value.expense_parameters ||= {};
  const profile = incomeAnalysis.value.building_profile;
  const expense = incomeAnalysis.value.expense_parameters;
  const structureKey = expense.replacement_cost_structure_key || inferIncomeCostStructureKey(profile.structure);
  const validGrades = residentialConstructionCostStandards.filter(item => item.structureKey === structureKey);
  let gradeKey = expense.replacement_cost_grade_key || defaultIncomeCostGradeKey(structureKey);
  if (!validGrades.some(item => item.gradeKey === gradeKey)) {
    gradeKey = validGrades[0]?.gradeKey || '';
  }
  const key = incomeCostStandardKeyFromParts(structureKey, gradeKey);
  const standard = residentialConstructionCostByKey[key] || validGrades[0] || residentialConstructionCostByKey.brick_concrete_1;
  expense.replacement_cost_standard_key = standard.key;
  expense.replacement_cost_structure_key = standard.structureKey;
  expense.replacement_cost_grade_key = standard.gradeKey;
  expense.replacement_cost_range_min = standard.min;
  expense.replacement_cost_range_max = standard.max;
  expense.replacement_cost_range_label = `${standard.min}-${standard.max}`;
  expense.replacement_cost_source_doc = '《湖南省建筑物建设成本参考标准研究成果》（湘房协〔2023〕3号）';
  if (resetAdopted || !String(expense.replacement_base_unit_cost || '').trim() || expense.replacement_cost_adopted_source === 'range_max_default') {
    expense.replacement_base_unit_cost = standard.max;
    expense.replacement_cost_adopted_source = 'range_max_default';
    expense.replacement_cost_override_reason = '';
  } else if (!expense.replacement_cost_adopted_source) {
    expense.replacement_cost_adopted_source = String(expense.replacement_base_unit_cost) === String(standard.max) ? 'range_max_default' : 'manual_override';
  }
  profile.structure = standard.structure;
};
const onIncomeStructureChange = () => {
  incomeAnalysis.value.expense_parameters ||= {};
  const expense = incomeAnalysis.value.expense_parameters;
  expense.replacement_cost_structure_key = inferIncomeCostStructureKey(incomeAnalysis.value?.building_profile?.structure);
  expense.replacement_cost_grade_key = '';
  const reset = expense.replacement_cost_adopted_source === 'range_max_default' || !String(expense.replacement_base_unit_cost || '').trim();
  syncIncomeCostStandard(reset);
};
const onIncomeCostGradeChange = () => {
  syncIncomeCostStandard(true);
};
const markIncomeReplacementCostManual = () => {
  incomeAnalysis.value.expense_parameters ||= {};
  incomeAnalysis.value.expense_parameters.replacement_cost_adopted_source = 'manual_override';
};
const resetIncomeReplacementCostToRangeMax = () => {
  syncIncomeCostStandard(true);
};
const ensureIncomeAnalysisDefaults = () => {
  incomeAnalysis.value.rent_factor_items ||= [];
  normalizeIncomeFactorStandards();
  incomeAnalysis.value.rent_instances ||= [];
  incomeAnalysis.value.rent_instances.forEach(item => {
    item.usage_key ||= inferRentalUsageKey(item.usage || form.land_usage.value);
    item.usage_other ||= item.usage_key === 'other' ? String(item.usage || '').trim() : '';
    onRentUsageChange(item);
    onRentTransactionDateChange(item);
  });
  incomeAnalysis.value.income_parameters ||= {};
  if (incomeAnalysis.value.income_parameters.vacancy_rate_range === undefined) {
    incomeAnalysis.value.income_parameters.vacancy_rate_range = '';
  }
  incomeAnalysis.value.expense_parameters ||= {};
  syncIncomeCostStandard(false);
  syncIncomeDerivedFields(false);
};

watch(
  () => [
    form.valuation_condition_type.value,
    form.valuation_date.value,
    form.building_area.value,
    form.land_area.value,
    form.set_plot_ratio.value,
  ],
  () => {
    syncIncomeDerivedFields(false);
    syncIncomeBuildingYears('');
  },
  { immediate: true }
);

watch(
  incomeAnalysis,
  (newVal) => {
    if (newVal) {
      form.income_cap_analysis.value = JSON.parse(JSON.stringify(newVal));
    }
  },
  { deep: true }
);

watch(
  marketAnalysis,
  (newVal) => {
    if (newVal) {
      form.market_comp_analysis.value = JSON.parse(JSON.stringify(newVal));
    }
  },
  { deep: true }
);

const applyIncomeAnalysisToForm = (analysis) => {
  incomeAnalysis.value = JSON.parse(JSON.stringify(analysis || {}));
  incomeAnalysis.value.rent_instances ||= [];
  incomeAnalysis.value.rent_factor_items ||= [];
  incomeAnalysis.value.building_profile ||= {};
  incomeAnalysis.value.income_parameters ||= {};
  incomeAnalysis.value.expense_parameters ||= {};
  incomeAnalysis.value.cap_rate_parameters ||= {};
  incomeAnalysis.value.income_results ||= {};
  ensureIncomeAnalysisDefaults();
  form.income_cap_analysis.value = JSON.parse(JSON.stringify(incomeAnalysis.value));
  form.income_cap_analysis.origin = 'generated';
  form.income_cap_analysis.is_dirty = false;
  if (analysis?.income_cap_price) {
    form.income_cap_price.value = analysis.income_cap_price;
    form.income_cap_price.origin = 'generated';
    form.income_cap_price.is_dirty = false;
  }
};

const calculateIncomeCapitalization = async () => {
  try {
    ensureIncomeAnalysisDefaults();
    form.income_cap_analysis.value = JSON.parse(JSON.stringify(incomeAnalysis.value || {}));
    const payload = buildFlatPayload();
    payload.income_cap_analysis = JSON.parse(JSON.stringify(incomeAnalysis.value || {}));
    const analysis = await apiJson('/api/income-capitalization/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload, overwrite: false })
    });
    applyIncomeAnalysisToForm(analysis);
    await loadValuationProcessDraft();
    showToast(analysis.complete ? '收益还原法测算已完成并通过确认。' : '收益还原法已试算，仍有租金实例、因素或图片待确认。', analysis.complete ? 'success' : 'warning');
  } catch (error) {
    showToast(`收益还原法计算失败：${error.message}`, 'error');
  }
};

// ===== 基准地价系数修正法=====
const benchmarkLinkedFormValues = () => ({
  plot_ratio: form.set_plot_ratio_display?.value || form.set_plot_ratio?.value || form.plot_ratio_display?.value || form.plot_ratio?.value || '',
  set_term_years: form.land_use_term_years?.value || form.land_use_term?.value || '',
  valuation_date: form.valuation_date?.value || '',
  set_development: form.land_development_set?.value || ''
});

const benchmarkLinkedPlotRatio = computed(() => benchmarkLinkedFormValues().plot_ratio);
const benchmarkLinkedUseTerm = computed(() => benchmarkLinkedFormValues().set_term_years);
const benchmarkLinkedValuationDate = computed(() => benchmarkLinkedFormValues().valuation_date);
const benchmarkLinkedSetDevelopment = computed(() => benchmarkLinkedFormValues().set_development);

const benchmarkBoolValue = (value) => (
  value === true
  || value === 1
  || ['1', 'true', 'yes', '是', '街角', 'y'].includes(String(value ?? '').trim().toLowerCase())
);

const formatBenchmarkDerivedNumber = (value, digits = 2) => {
  if (!Number.isFinite(value)) return '';
  const fixed = value.toFixed(digits);
  return fixed.replace(/\.?0+$/, '');
};

const benchmarkDerivedFrontageDepth = () => {
  const area = parseCostNumber(
    benchmarkAnalysis.value?.parameters?.commercial_area_m2
    || benchmarkAnalysis.value?.commercial_area_m2
    || form.land_area.value
    || benchmarkAnalysis.value?.parameters?.land_area
    || benchmarkAnalysis.value?.land_area
  );
  const width = parseCostNumber(benchmarkAnalysis.value?.frontage_width_m || benchmarkAnalysis.value?.parameters?.frontage_width_m);
  if (!Number.isFinite(area) || !Number.isFinite(width) || area <= 0 || width <= 0) return '';
  return formatBenchmarkDerivedNumber(area / width, 2);
};

const benchmarkDefaultStandardDepth = (roadType) => {
  const text = String(roadType || '').trim();
  if (text.includes('主干道')) return '20';
  if (text.includes('次干道')) return '16';
  if (text.includes('支路')) return '12';
  return '';
};

const benchmarkRoadTypeFromGrade = (value) => {
  const text = String(value || '').trim();
  if (text.includes('主干道')) return '主干道';
  if (text.includes('次干道')) return '次干道';
  if (text.includes('支路')) return '支路';
  return '';
};

const syncBenchmarkCornerFields = () => {
  benchmarkAnalysis.value.parameters ||= {};
  if (benchmarkAnalysis.value.corner_route_price_a === undefined || benchmarkAnalysis.value.corner_route_price_a === null) {
    benchmarkAnalysis.value.corner_route_price_a = benchmarkAnalysis.value.parameters.corner_route_price_a || '';
  }
  if (benchmarkAnalysis.value.corner_route_price_b === undefined || benchmarkAnalysis.value.corner_route_price_b === null) {
    benchmarkAnalysis.value.corner_route_price_b = benchmarkAnalysis.value.parameters.corner_route_price_b || '';
  }
  const a = parseCostNumber(benchmarkAnalysis.value.corner_route_price_a);
  const b = parseCostNumber(benchmarkAnalysis.value.corner_route_price_b);
  benchmarkAnalysis.value.parameters.corner_route_price_a = benchmarkAnalysis.value.corner_route_price_a;
  benchmarkAnalysis.value.parameters.corner_route_price_b = benchmarkAnalysis.value.corner_route_price_b;
  if (Number.isFinite(a) && a > 0 && Number.isFinite(b) && b > 0) {
    const main = Math.max(a, b);
    const side = Math.min(a, b);
    benchmarkAnalysis.value.parameters.corner_main_route_price = formatBenchmarkDerivedNumber(main, 2);
    benchmarkAnalysis.value.parameters.corner_side_route_price = formatBenchmarkDerivedNumber(side, 2);
    benchmarkAnalysis.value.parameters.corner_price_ratio = formatBenchmarkDerivedNumber(main / side, 4);
    benchmarkAnalysis.value.corner_price_ratio = benchmarkAnalysis.value.parameters.corner_price_ratio;
  } else {
    benchmarkAnalysis.value.parameters.corner_main_route_price = '';
    benchmarkAnalysis.value.parameters.corner_side_route_price = '';
    benchmarkAnalysis.value.parameters.corner_price_ratio = '';
    benchmarkAnalysis.value.corner_price_ratio = '';
  }
};

const benchmarkFrontageStandardDepthValue = () => (
  benchmarkSelectedRouteSegment.value?.standard_depth
  || benchmarkAnalysis.value?.parameters?.frontage_standard_depth_m
  || benchmarkAnalysis.value?.frontage_standard_depth_m
  || benchmarkDefaultStandardDepth(benchmarkRouteRoadTypeDisplay.value)
  || ''
);

const syncBenchmarkCommercialSplitFields = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.frontage_relation ||= benchmarkAnalysis.value.parameters.frontage_relation || 'adjacent';
  benchmarkAnalysis.value.parameters.frontage_relation = benchmarkAnalysis.value.frontage_relation;
  const commercialArea = parseCostNumber(
    benchmarkAnalysis.value.parameters.commercial_area_m2
    || benchmarkAnalysis.value.commercial_area_m2
    || form.land_area.value
    || benchmarkAnalysis.value.parameters.land_area
  );
  const standardDepth = parseCostNumber(benchmarkFrontageStandardDepthValue());
  const width = parseCostNumber(benchmarkAnalysis.value.frontage_width_m || benchmarkAnalysis.value.parameters.frontage_width_m);
  const manualDepth = parseCostNumber(benchmarkAnalysis.value.frontage_depth_m || benchmarkAnalysis.value.parameters.frontage_depth_m);
  const useManualDepth = benchmarkAnalysis.value.frontage_relation === 'setback';
  const splitDepthForArea = useManualDepth && Number.isFinite(manualDepth) && manualDepth > 0 && (!Number.isFinite(standardDepth) || manualDepth <= standardDepth)
    ? manualDepth
    : standardDepth;
  benchmarkAnalysis.value.parameters.commercial_area_m2 = Number.isFinite(commercialArea) && commercialArea > 0 ? formatBenchmarkDerivedNumber(commercialArea, 2) : '';
  benchmarkAnalysis.value.commercial_area_m2 = benchmarkAnalysis.value.parameters.commercial_area_m2;
  benchmarkAnalysis.value.parameters.frontage_standard_depth_m = Number.isFinite(standardDepth) && standardDepth > 0 ? formatBenchmarkDerivedNumber(standardDepth, 2) : '';
  benchmarkAnalysis.value.frontage_standard_depth_m = benchmarkAnalysis.value.parameters.frontage_standard_depth_m;
  if (Number.isFinite(commercialArea) && commercialArea > 0 && Number.isFinite(splitDepthForArea) && splitDepthForArea > 0 && Number.isFinite(width) && width > 0) {
    const frontageArea = splitDepthForArea * width;
    const nonFrontageArea = commercialArea - frontageArea;
    benchmarkAnalysis.value.parameters.frontage_area_m2 = formatBenchmarkDerivedNumber(frontageArea, 2);
    benchmarkAnalysis.value.parameters.non_frontage_area_m2 = formatBenchmarkDerivedNumber(nonFrontageArea, 2);
    benchmarkAnalysis.value.frontage_area_m2 = benchmarkAnalysis.value.parameters.frontage_area_m2;
    benchmarkAnalysis.value.non_frontage_area_m2 = benchmarkAnalysis.value.parameters.non_frontage_area_m2;
  } else {
    benchmarkAnalysis.value.parameters.frontage_area_m2 = '';
    benchmarkAnalysis.value.parameters.non_frontage_area_m2 = '';
    benchmarkAnalysis.value.frontage_area_m2 = '';
    benchmarkAnalysis.value.non_frontage_area_m2 = '';
  }
  return syncBenchmarkFrontageDepth();
};

const syncBenchmarkFrontageDepth = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.frontage_relation ||= benchmarkAnalysis.value.parameters.frontage_relation || 'adjacent';
  benchmarkAnalysis.value.parameters.frontage_relation = benchmarkAnalysis.value.frontage_relation;
  if (benchmarkAnalysis.value.frontage_relation === 'setback') {
    const manual = benchmarkAnalysis.value.frontage_depth_m || benchmarkAnalysis.value.parameters.frontage_depth_m || '';
    benchmarkAnalysis.value.frontage_depth_m = manual;
    benchmarkAnalysis.value.parameters.frontage_depth_m = manual;
    benchmarkAnalysis.value.parameters.frontage_depth_source = manual ? 'manual' : '';
    return manual;
  }
  const derived = benchmarkDerivedFrontageDepth();
  benchmarkAnalysis.value.frontage_depth_m = derived;
  benchmarkAnalysis.value.parameters.frontage_depth_m = derived;
  benchmarkAnalysis.value.parameters.frontage_depth_source = derived ? 'auto_by_area_width' : '';
  return derived;
};

const BENCHMARK_STATUTORY_TERM_RULES = {
  '住宅': '70',
  '住宅用地': '70',
  '居住用地': '70',
  '商业': '40',
  '商服用地': '40',
  '商业用地': '40',
  '商业服务业用地': '40',
  '工业用地': '50',
  '工矿用地': '50',
  '仓储用地': '50',
  '公共管理与公共服务用地': '50',
  '交通运输用地': '50',
  '公用设施用地': '50',
  '绿地与开敞空间用地': '50',
  '特殊用地': '50'
};

const benchmarkStatutoryTermForUsage = (usage) => {
  const text = String(usage || '').trim();
  if (!text) return '';
  if (BENCHMARK_STATUTORY_TERM_RULES[text]) return BENCHMARK_STATUTORY_TERM_RULES[text];
  const matched = Object.entries(BENCHMARK_STATUTORY_TERM_RULES).find(([key]) => key && text.includes(key));
  return matched ? matched[1] : '';
};

const benchmarkLegalTermDisplay = computed(() => (
  benchmarkStatutoryTermForUsage(benchmarkAnalysis.value?.land_use_type)
  || benchmarkAnalysis.value?.parameters?.legal_term_years
  || ''
));

const syncBenchmarkLinkedParameters = () => {
  benchmarkAnalysis.value.parameters ||= {};
  const linked = benchmarkLinkedFormValues();
  benchmarkAnalysis.value.parameters.plot_ratio = linked.plot_ratio || '';
  benchmarkAnalysis.value.parameters.set_term_years = linked.set_term_years || '';
  benchmarkAnalysis.value.parameters.valuation_date = linked.valuation_date || '';
  benchmarkAnalysis.value.parameters.set_development = linked.set_development || '';
  benchmarkAnalysis.value.parameters.land_area = form.land_area.value || '';
  benchmarkAnalysis.value.parameters.land_area_mode = form.land_area_mode.value || '';
  benchmarkAnalysis.value.parameters.legal_term_years = benchmarkStatutoryTermForUsage(benchmarkAnalysis.value.land_use_type) || '';
  if (benchmarkAnalysis.value.land_use_type === '商业服务业用地') {
    benchmarkAnalysis.value.frontage_mode ||= benchmarkAnalysis.value.parameters.frontage_mode || 'non_street';
    benchmarkAnalysis.value.parameters.frontage_mode = benchmarkAnalysis.value.frontage_mode;
    benchmarkAnalysis.value.parameters.route_segment_id = benchmarkAnalysis.value.route_segment_id || benchmarkAnalysis.value.parameters.route_segment_id || '';
    benchmarkAnalysis.value.parameters.ku_grade = benchmarkAnalysis.value.ku_grade || benchmarkAnalysis.value.parameters.ku_grade || '';
    benchmarkAnalysis.value.parameters.frontage_width_m = benchmarkAnalysis.value.frontage_width_m || benchmarkAnalysis.value.parameters.frontage_width_m || '';
    benchmarkAnalysis.value.parameters.frontage_relation = benchmarkAnalysis.value.frontage_relation || benchmarkAnalysis.value.parameters.frontage_relation || 'adjacent';
    benchmarkAnalysis.value.parameters.route_road_grade = benchmarkAnalysis.value.route_road_grade || benchmarkAnalysis.value.parameters.route_road_grade || '';
    if (['street_route_price', 'route_price_plus_non_street'].includes(benchmarkAnalysis.value.frontage_mode)) {
      syncBenchmarkCommercialSplitFields();
    } else {
      benchmarkAnalysis.value.frontage_depth_m = '';
      benchmarkAnalysis.value.parameters.frontage_depth_m = '';
      ['commercial_area_m2', 'frontage_standard_depth_m', 'frontage_area_m2', 'non_frontage_area_m2'].forEach(key => {
        benchmarkAnalysis.value[key] = '';
        benchmarkAnalysis.value.parameters[key] = '';
      });
    }
    benchmarkAnalysis.value.parameters.corner_price_ratio = benchmarkAnalysis.value.corner_price_ratio || benchmarkAnalysis.value.parameters.corner_price_ratio || '';
  }
};

const jumpToBenchmarkLinkedField = (field) => {
  scrollToField(field);
};

const ensureBenchmarkAnalysisDefaults = () => {
  if (Array.isArray(benchmarkAnalysis.value.results)) {
    const resultMap = {};
    benchmarkAnalysis.value.result_values ||= {};
    benchmarkAnalysis.value.results.forEach(item => {
      if (item?.key) {
        resultMap[item.key] = item.value;
        benchmarkAnalysis.value.result_values[item.key] = item.value;
      }
    });
    benchmarkAnalysis.value.results = resultMap;
  }
  if (Array.isArray(benchmarkAnalysis.value.tables)) {
    const tableMap = {};
    benchmarkAnalysis.value.tables.forEach(item => {
      if (item?.key) tableMap[item.key] = item;
    });
    if (tableMap.benchmark_base_price_table && !tableMap.base_price_table) {
      tableMap.base_price_table = tableMap.benchmark_base_price_table;
    }
    benchmarkAnalysis.value.tables = tableMap;
  }
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.regional_factors ||= [];
  benchmarkAnalysis.value.individual_factors ||= {};
  benchmarkAnalysis.value.tables ||= {};
  benchmarkAnalysis.value.results ||= {};
  benchmarkAnalysis.value.result_values ||= {};
  benchmarkAnalysis.value.coverage_scope ||= benchmarkAnalysis.value.parameters.coverage_scope || '城区';
  benchmarkAnalysis.value.township_grade ||= benchmarkAnalysis.value.parameters.township_grade || '';
  benchmarkAnalysis.value.land_use_type ||= benchmarkAnalysis.value.parameters.land_use_type || form.land_usage_price_class?.value || '居住用地';
  benchmarkAnalysis.value.land_level ||= benchmarkAnalysis.value.parameters.land_level || '二级';
  if (benchmarkAnalysis.value.land_use_type === '商业服务业用地') {
    benchmarkAnalysis.value.frontage_mode ||= benchmarkAnalysis.value.parameters.frontage_mode || 'non_street';
  }
  benchmarkAnalysis.value.route_segment_id ||= benchmarkAnalysis.value.parameters.route_segment_id || '';
  benchmarkAnalysis.value.ku_grade ||= benchmarkAnalysis.value.parameters.ku_grade || benchmarkAnalysis.value.individual_factors?.surrounding_land_use?.grade || '';
  benchmarkAnalysis.value.frontage_depth_m ||= benchmarkAnalysis.value.parameters.frontage_depth_m || '';
  benchmarkAnalysis.value.frontage_width_m ||= benchmarkAnalysis.value.parameters.frontage_width_m || '';
  benchmarkAnalysis.value.frontage_relation ||= benchmarkAnalysis.value.parameters.frontage_relation || 'adjacent';
  benchmarkAnalysis.value.route_road_grade ||= benchmarkAnalysis.value.parameters.route_road_grade || '';
  benchmarkAnalysis.value.commercial_area_m2 ||= benchmarkAnalysis.value.parameters.commercial_area_m2 || '';
  benchmarkAnalysis.value.frontage_standard_depth_m ||= benchmarkAnalysis.value.parameters.frontage_standard_depth_m || '';
  benchmarkAnalysis.value.frontage_area_m2 ||= benchmarkAnalysis.value.parameters.frontage_area_m2 || '';
  benchmarkAnalysis.value.non_frontage_area_m2 ||= benchmarkAnalysis.value.parameters.non_frontage_area_m2 || '';
  benchmarkAnalysis.value.corner_route_price_a ||= benchmarkAnalysis.value.parameters.corner_route_price_a || '';
  benchmarkAnalysis.value.corner_route_price_b ||= benchmarkAnalysis.value.parameters.corner_route_price_b || '';
  benchmarkAnalysis.value.corner_price_ratio ||= benchmarkAnalysis.value.parameters.corner_price_ratio || '';
  benchmarkAnalysis.value.is_corner = benchmarkBoolValue(benchmarkAnalysis.value.is_corner);
  syncBenchmarkLinkedParameters();
  syncBenchmarkCornerFields();
  benchmarkAnalysis.value.map_image_ids ||= [];
  benchmarkAnalysis.value.map_images ||= [];
};

const benchmarkBaseRowUseType = (row) => row?.use_type || row?.['用地类型'] || row?.land_use_type || '';

const benchmarkBaseRowValue = (row, level, index) => {
  if (!row) return '';
  if (row[level] !== undefined && row[level] !== null) return row[level];
  if (Array.isArray(row.values)) return row.values[index] ?? '';
  return '';
};

const benchmarkIsCommercial = computed(() => benchmarkAnalysis.value?.land_use_type === '商业服务业用地');

const benchmarkIsSplitRoutePrice = computed(() => (
  benchmarkIsCommercial.value && benchmarkAnalysis.value?.frontage_mode === 'route_price_plus_non_street'
));

const benchmarkIsSingleRoutePrice = computed(() => (
  benchmarkIsCommercial.value && benchmarkAnalysis.value?.frontage_mode === 'street_route_price'
));

const benchmarkUsesRoutePrice = computed(() => (
  benchmarkIsSingleRoutePrice.value || benchmarkIsSplitRoutePrice.value
));

const benchmarkRouteSegments = computed(() => {
  const rows = benchmarkAnalysis.value?.tables?.benchmark_route_price_table?.rows || [];
  return rows.map(row => ({
    id: row.id || row.code || row['编号'] || '',
    road_name: row.road_name || row['道路名称'] || '',
    route_start: row.route_start || row['路线起点'] || row['起点'] || '',
    route_end: row.route_end || row['路线终点'] || row['终点'] || '',
      level: row.level || row['所属级别'] || '',
    road_type: row.road_type || row['道路类型'] || '',
    standard_depth: row.standard_depth || row['标准深度'] || '',
      route_price: row.route_price || row['路线价'] || ''
  })).filter(row => row.id);
});

const benchmarkSelectedRouteSegment = computed(() => (
  benchmarkRouteSegments.value.find(item => item.id === benchmarkAnalysis.value?.route_segment_id) || null
));

const benchmarkRouteRoadTypeDisplay = computed(() => (
  benchmarkSelectedRouteSegment.value?.road_type
  || benchmarkAnalysis.value?.parameters?.route_road_type
  || benchmarkAnalysis.value?.route_road_type
  || benchmarkRoadTypeFromGrade(benchmarkAnalysis.value?.parameters?.route_road_grade || benchmarkAnalysis.value?.route_road_grade)
  || ''
));

const benchmarkRouteSegmentLabel = (segment) => {
  if (!segment) return '';
  return `${segment.id} ${segment.road_name || '未命名道路'} ${segment.route_start || ''}-${segment.route_end || ''} / ${segment.route_price || '待校核'}元/㎡`;
};

const benchmarkKuOptions = computed(() => {
  const factorOptions = benchmarkAnalysis.value?.individual_factors?.surrounding_land_use?.options || [];
  if (factorOptions.length) return factorOptions;
  const table = benchmarkAnalysis.value?.tables?.benchmark_surrounding_land_use_table || {};
  const columns = (table.columns || []).filter(col => col && col !== '指标标准');
  if (columns.length) {
    const descRow = (table.rows || []).find(row => row['指标标准'] === '指标说明') || {};
    return columns.map(label => ({ label, grade: label, description: descRow[label] || '' }));
  }
  return ['优', '较优', '一般', '较劣', '劣'].map(label => ({ label, grade: label, description: '' }));
});

const benchmarkLandUseTypeOptions = computed(() => {
  const fromTable = benchmarkAnalysis.value?.tables?.base_price_table?.use_types || [];
  const base = fromTable.length
    ? fromTable
    : ['商业服务业用地', '居住用地', '工矿用地', '仓储用地', '公共管理与公共服务用地', '公用设施用地'];
  const current = benchmarkAnalysis.value?.land_use_type;
  return Array.from(new Set([...base, current, '其他用途'].filter(Boolean)));
});

const benchmarkSupportSummary = computed(() => {
  const items = (benchmarkAnalysis.value?.support_missing_items || []).map(item => String(item || '')).filter(Boolean);
  if (benchmarkAnalysis.value?.support_status === 'unsupported') {
    return items[0] || '当前地区暂未纳入基准地价系数修正法结构化配置。';
  }
  if (!items.length) return '用途、级别或修正体系仍待校核。';
  const regionCount = items.filter(item => item.includes('区域因素')).length;
  const individualCount = items.filter(item => (
    item.includes('宗地面积')
    || item.includes('宗地形状')
    || item.includes('景观环境')
      || item.includes('建筑物朝向')
  )).length;
  const baseCount = items.length - regionCount - individualCount;
  const parts = [];
  if (baseCount > 0) parts.push(`基础参数 ${baseCount} 项`);
  if (regionCount > 0) parts.push(`区域因素 ${regionCount} 项`);
  if (individualCount > 0) parts.push(`个别因素 ${individualCount} 项`);
  return `仍有${parts.join('、')}待校核；下方预警列表可逐项跳转。`;
});

const benchmarkSupportActionTarget = (method) => {
  const target = (method?.warnings || [])
    .map(item => warningTarget(item))
    .find(item => String(item || '').startsWith('benchmark_corr_analysis.') || item === 'valuation_date');
  return target || 'benchmark_corr_analysis.land_use_type';
};

const benchmarkResultValue = (key) => (
  benchmarkAnalysis.value?.result_values?.[key]
  || benchmarkAnalysis.value?.results?.[key]
  || ''
);

const benchmarkFormulaSymbol = computed(() => (
  benchmarkAnalysis.value?.result_values?.formula_symbol
  || (benchmarkAnalysis.value?.land_use_type === '居住用地' ? 'P住' : (benchmarkIsCommercial.value ? 'P商' : 'P'))
));

const benchmarkPriceDisplay = computed(() => (
  benchmarkResultValue('benchmark_corr_price')
  || benchmarkAnalysis.value?.benchmark_corr_price
  || ''
));

const benchmarkFormulaPreview = computed(() => (
  benchmarkAnalysis.value?.parameters?.formula_text
  || (benchmarkIsSplitRoutePrice.value
    ? '1、商业服务业用地（临街）\nP商=路线价×Ky×Kv×Kt×Ks×Ka×Kc×Kk×Kd×Ku＋Kf\n2、商业服务业用地（不临街）\nP商=级别基准地价×（1+∑Ki）×Ky×Kv×Kt×Ks×Ka×Ku＋Kf'
    : benchmarkIsSingleRoutePrice.value
    ? '1、商业服务业用地（临街）\nP商=路线价×Ky×Kv×Kt×Ks×Ka×Kc×Kk×Kd×Ku＋Kf'
    : benchmarkIsCommercial.value
      ? '2、商业服务业用地（不临街）\nP商=级别基准地价×（1+∑Ki）×Ky×Kv×Kt×Ks×Ka×Ku＋Kf'
      : `${benchmarkFormulaSymbol.value}=${benchmarkFormulaFactorKeys.value
        .filter(key => key !== 'kf')
        .map(benchmarkFormulaFactorLabel)
        .join('×')}＋Kf`)
));

const benchmarkFormulaFactorKeys = computed(() => {
  const usage = benchmarkAnalysis.value?.land_use_type || '';
  if (benchmarkIsSingleRoutePrice.value) return ['route_price', 'ky', 'kv', 'kt', 'ks', 'ka', 'kc', 'kk', 'kd', 'ku', 'kf'];
  if (benchmarkIsCommercial.value) return ['base', 'ki', 'ky', 'kv', 'kt', 'ks', 'ka', 'ku', 'kf'];
  if (usage === '居住用地') return ['base', 'ki', 'ky', 'kv', 'kt', 'ks', 'ka', 'ke', 'kto', 'kf'];
  if (usage === '公共管理与公共服务用地') return ['base', 'ki', 'ky', 'kv', 'kt', 'ks', 'ka', 'kf'];
  if (usage === '公用设施用地') return ['base', 'ky', 'kt', 'ks', 'ka', 'kf'];
  if (usage === '工矿用地' || usage === '仓储用地') return ['base', 'ki', 'ky', 'kt', 'ks', 'ka', 'kf'];
  return ['base', 'ki', 'ky', 'kt', 'ks', 'ka', 'kf'];
});

const benchmarkFormulaFactorLabel = (key) => ({
  base: '级别基准地价',
  route_price: '路线价',
  ki: '（1+∑Ki）',
  ky: 'Ky',
  kv: 'Kv',
  kt: 'Kt',
  ks: 'Ks',
  ka: 'Ka',
  kc: 'Kc',
  kk: 'Kk',
  kd: 'Kd',
  ku: 'Ku',
  ke: 'Ke',
  kto: 'Kto'
}[key] || key);

const benchmarkFormulaFactorValue = (key, parameters) => {
  if (key === 'base') return parameters.base_land_price;
  if (key === 'route_price') return parameters.route_price;
  if (key === 'ki') return `(1+${benchmarkRegionalSum.value || parameters.sum_ki || '-'}%)`;
  return parameters[key];
};

const benchmarkFormulaValuePreview = computed(() => {
  const p = benchmarkAnalysis.value?.parameters || {};
  if (benchmarkIsSplitRoutePrice.value) {
    const routePrice = benchmarkAnalysis.value?.result_values?.route_component_price || p.route_component_price || '-';
    const nonStreetPrice = benchmarkAnalysis.value?.result_values?.non_street_component_price || p.non_street_component_price || '-';
    const frontageArea = p.frontage_area_m2 || benchmarkAnalysis.value?.frontage_area_m2 || '-';
    const nonFrontageArea = p.non_frontage_area_m2 || benchmarkAnalysis.value?.non_frontage_area_m2 || '-';
    const commercialArea = p.commercial_area_m2 || benchmarkAnalysis.value?.commercial_area_m2 || '-';
    return `=(${routePrice}×${frontageArea}+${nonStreetPrice}×${nonFrontageArea})÷${commercialArea}`;
  }
  const values = benchmarkFormulaFactorKeys.value
    .filter(key => key !== 'kf')
    .map(key => benchmarkFormulaFactorValue(key, p));
  return `=${values.map(value => value || '-').join('×')}+${p.kf || '0'}`;
});

const benchmarkTownshipGradeOptions = computed(() => {
  const table = benchmarkAnalysis.value?.tables?.benchmark_township_base_price_table || {};
  const grades = table.township_grades || [];
  return grades.length ? grades : ['一等', '二等', '三等'];
});

const benchmarkMapImageIdsText = computed({
  get: () => (benchmarkAnalysis.value?.map_image_ids || []).join('；'),
  set: (value) => {
    benchmarkAnalysis.value.map_image_ids = String(value || '')
    .split(/[；;\s]+/)
      .map(item => item.trim())
      .filter(Boolean);
  }
});

const triggerBenchmarkMapUpload = () => {
  document.getElementById('benchmark-map-image-upload')?.click?.();
};

const handleBenchmarkMapUpload = (event) => {
  const files = Array.from(event.target.files || []);
  event.target.value = '';
  if (!files.length) return;
  ensureBenchmarkAnalysisDefaults();
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = () => {
      benchmarkAnalysis.value.map_images ||= [];
      benchmarkAnalysis.value.map_images.push({
        id: `benchmark_map_${Date.now()}_${Math.random().toString(16).slice(2)}`,
        name: file.name,
        data: reader.result
      });
      onBenchmarkMapIdsChange();
    };
    reader.readAsDataURL(file);
  });
};

const removeBenchmarkMapImage = (index) => {
  benchmarkAnalysis.value.map_images?.splice(index, 1);
  onBenchmarkMapIdsChange();
};

const cloneBenchmarkAnalysisForStorage = (source = {}) => {
  const { map_images: _mapImages, ...lightweight } = source || {};
  return JSON.parse(JSON.stringify(lightweight || {}));
};

const persistBenchmarkAnalysisSnapshot = ({ origin = 'generated', dirty = false } = {}) => {
  form.benchmark_corr_analysis.value = cloneBenchmarkAnalysisForStorage(benchmarkAnalysis.value);
  form.benchmark_corr_analysis.origin = origin;
  form.benchmark_corr_analysis.is_dirty = dirty;
};

const applyBenchmarkAnalysisToForm = (analysis) => {
  const previousMapImages = benchmarkAnalysis.value?.map_images || [];
  benchmarkAnalysis.value = JSON.parse(JSON.stringify(analysis || {}));
  if (!(benchmarkAnalysis.value.map_images || []).length && previousMapImages.length) {
    benchmarkAnalysis.value.map_images = previousMapImages;
  }
  ensureBenchmarkAnalysisDefaults();
  persistBenchmarkAnalysisSnapshot({ origin: 'generated', dirty: false });
  const price = analysis?.benchmark_corr_price
    || analysis?.result_values?.benchmark_corr_price
    || analysis?.results?.benchmark_corr_price
    || analysis?.results?.p_residential;
  if (price) {
    form.benchmark_corr_price.value = String(price);
    form.benchmark_corr_price.origin = 'generated';
    form.benchmark_corr_price.is_dirty = false;
  }
};

const buildBenchmarkAnalysisPayload = () => {
  ensureBenchmarkAnalysisDefaults();
  const analysis = cloneBenchmarkAnalysisForStorage(benchmarkAnalysis.value || {});
  analysis.parameters ||= {};
  const linked = benchmarkLinkedFormValues();
  analysis.parameters.plot_ratio = linked.plot_ratio || '';
  analysis.parameters.set_term_years = linked.set_term_years || '';
  analysis.parameters.valuation_date = linked.valuation_date || '';
  analysis.parameters.set_development = linked.set_development || '';
  analysis.parameters.land_area = form.land_area.value || '';
  analysis.parameters.land_area_mode = form.land_area_mode.value || '';
  analysis.land_use_type = benchmarkAnalysis.value.land_use_type || analysis.parameters.land_use_type || '';
  analysis.parameters.legal_term_years = benchmarkStatutoryTermForUsage(analysis.land_use_type) || '';
  analysis.land_level = benchmarkAnalysis.value.land_level || analysis.parameters.land_level || '';
  analysis.coverage_scope = benchmarkAnalysis.value.coverage_scope || analysis.parameters.coverage_scope || '城区';
  analysis.township_grade = benchmarkAnalysis.value.township_grade || analysis.parameters.township_grade || '';
  const isCommercialPayload = analysis.land_use_type === '商业服务业用地';
  analysis.frontage_mode = isCommercialPayload
    ? (benchmarkAnalysis.value.frontage_mode || analysis.parameters.frontage_mode || 'non_street')
    : 'non_street';
  analysis.parameters.frontage_mode = analysis.frontage_mode;
  const selectedRoute = benchmarkSelectedRouteSegment.value;
  analysis.route_segment_id = benchmarkAnalysis.value.route_segment_id || analysis.parameters.route_segment_id || '';
  analysis.route_price = selectedRoute?.route_price || analysis.parameters.route_price || benchmarkAnalysis.value.route_price || '';
  analysis.route_price_source_note = analysis.parameters.route_price_source_note || benchmarkAnalysis.value.route_price_source_note || '';
  analysis.route_road_grade = benchmarkAnalysis.value.route_road_grade || analysis.parameters.route_road_grade || '';
  analysis.parameters.route_road_grade = analysis.route_road_grade;
  analysis.route_road_type = selectedRoute?.road_type || analysis.parameters.route_road_type || benchmarkRoadTypeFromGrade(analysis.route_road_grade) || benchmarkAnalysis.value.route_road_type || '';
  analysis.parameters.route_road_type = analysis.route_road_type;
  analysis.ku_grade = benchmarkAnalysis.value.ku_grade || analysis.parameters.ku_grade || '';
  analysis.frontage_width_m = benchmarkAnalysis.value.frontage_width_m || analysis.parameters.frontage_width_m || '';
  analysis.parameters.frontage_width_m = analysis.frontage_width_m;
  analysis.frontage_relation = benchmarkAnalysis.value.frontage_relation || analysis.parameters.frontage_relation || 'adjacent';
  analysis.parameters.frontage_relation = analysis.frontage_relation;
  if (isCommercialPayload && ['street_route_price', 'route_price_plus_non_street'].includes(analysis.frontage_mode)) {
    syncBenchmarkCommercialSplitFields();
    analysis.frontage_depth_m = benchmarkAnalysis.value.frontage_depth_m || analysis.parameters.frontage_depth_m || '';
    analysis.parameters.frontage_depth_m = analysis.frontage_depth_m;
    analysis.parameters.frontage_standard_depth_m = benchmarkAnalysis.value.parameters?.frontage_standard_depth_m || analysis.parameters.frontage_standard_depth_m || selectedRoute?.standard_depth || benchmarkDefaultStandardDepth(analysis.route_road_type) || '';
    analysis.frontage_standard_depth_m = analysis.parameters.frontage_standard_depth_m;
    ['commercial_area_m2', 'frontage_area_m2', 'non_frontage_area_m2', 'frontage_average_depth_m'].forEach(key => {
      analysis.parameters[key] = benchmarkAnalysis.value.parameters?.[key] || analysis.parameters[key] || '';
      analysis[key] = benchmarkAnalysis.value[key] || analysis.parameters[key] || '';
    });
  } else {
    analysis.frontage_depth_m = '';
    analysis.parameters.frontage_depth_m = '';
    ['commercial_area_m2', 'frontage_standard_depth_m', 'frontage_area_m2', 'non_frontage_area_m2', 'frontage_average_depth_m'].forEach(key => {
      analysis.parameters[key] = '';
      analysis[key] = '';
    });
  }
  if (!isCommercialPayload) {
    [
      'route_segment_id',
      'route_price',
      'route_price_source',
      'route_price_source_note',
      'route_road_grade',
      'route_road_type',
      'ku_grade',
      'frontage_width_m',
      'frontage_relation',
      'kd',
      'kk',
      'kc',
      'ku'
    ].forEach(key => {
      analysis[key] = '';
      analysis.parameters[key] = '';
    });
  }
  analysis.is_corner = isCommercialPayload ? benchmarkBoolValue(benchmarkAnalysis.value.is_corner) : false;
  if (isCommercialPayload) syncBenchmarkCornerFields();
  analysis.corner_route_price_a = isCommercialPayload ? (benchmarkAnalysis.value.corner_route_price_a || analysis.parameters.corner_route_price_a || '') : '';
  analysis.corner_route_price_b = isCommercialPayload ? (benchmarkAnalysis.value.corner_route_price_b || analysis.parameters.corner_route_price_b || '') : '';
  analysis.corner_main_route_price = isCommercialPayload ? (benchmarkAnalysis.value.parameters?.corner_main_route_price || analysis.parameters.corner_main_route_price || '') : '';
  analysis.corner_side_route_price = isCommercialPayload ? (benchmarkAnalysis.value.parameters?.corner_side_route_price || analysis.parameters.corner_side_route_price || '') : '';
  analysis.corner_price_ratio = isCommercialPayload ? (benchmarkAnalysis.value.corner_price_ratio || analysis.parameters.corner_price_ratio || '') : '';
  ['corner_route_price_a', 'corner_route_price_b', 'corner_main_route_price', 'corner_side_route_price', 'corner_price_ratio'].forEach(key => {
    analysis.parameters[key] = analysis[key] || analysis.parameters[key] || '';
  });
  analysis.plot_ratio = analysis.parameters.plot_ratio;
  analysis.set_term_years = analysis.parameters.set_term_years;
  analysis.land_use_term = analysis.set_term_years;
  analysis.land_area = analysis.parameters.land_area;
  analysis.land_area_mode = analysis.parameters.land_area_mode;
  analysis.valuation_date = analysis.parameters.valuation_date;
  analysis.land_development_set = analysis.parameters.set_development;
  analysis.development_adjustment = analysis.parameters.kf ?? analysis.development_adjustment ?? '';
  (analysis.regional_factors || []).forEach(factor => {
    factor.grade = factor.level || factor.grade || '';
  });
  analysis.region_factor_selections = (analysis.regional_factors || []).map(factor => ({
    ...factor,
    grade: factor.level || factor.grade || '',
    level: factor.level || factor.grade || ''
  }));
  const individual = analysis.individual_factors || {};
  analysis.area_grade = individual.area?.level || individual.area?.grade || analysis.area_grade || '';
  analysis.shape_grade = individual.shape?.level || individual.shape?.grade || analysis.shape_grade || '';
  analysis.landscape_grade = individual.landscape?.level || individual.landscape?.grade || analysis.landscape_grade || '';
  analysis.orientation = individual.orientation?.level || individual.orientation?.grade || analysis.orientation || '';
  return cloneBenchmarkAnalysisForStorage(analysis);
};

const benchmarkCorrectionApiCall = async (options = {}) => {
  const payload = buildFlatPayload();
  const analysisPayload = buildBenchmarkAnalysisPayload();
  payload.benchmark_corr_analysis = analysisPayload;
  payload.land_use_type = analysisPayload.land_use_type;
  payload.land_level = analysisPayload.land_level;
  payload.set_plot_ratio = analysisPayload.plot_ratio || payload.set_plot_ratio;
  payload.land_use_term_years = analysisPayload.set_term_years || payload.land_use_term_years;
  payload.land_area = form.land_area.value || payload.land_area;
  payload.land_area_mode = form.land_area_mode.value || payload.land_area_mode;
  payload.valuation_date = analysisPayload.valuation_date || payload.valuation_date;
  payload.land_development_set = analysisPayload.land_development_set || payload.land_development_set;
  return apiJson('/api/benchmark-correction/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: payload, overwrite: false }),
    signal: options.signal
  });
};

let benchmarkRecalcTimer = null;
const benchmarkInteractiveDirty = ref(false);
let benchmarkRequestSeq = 0;
let benchmarkSilentAbortController = null;

const calculateBenchmarkCorrectionSilent = async (requestSeq = ++benchmarkRequestSeq) => {
  if (benchmarkSilentAbortController) benchmarkSilentAbortController.abort();
  const controller = new AbortController();
  benchmarkSilentAbortController = controller;
  try {
    const analysis = await benchmarkCorrectionApiCall({ signal: controller.signal });
    if (requestSeq !== benchmarkRequestSeq) return null;
    applyBenchmarkAnalysisToForm(analysis);
    benchmarkInteractiveDirty.value = false;
    return analysis;
  } catch (error) {
    if (error?.name === 'AbortError') return null;
    return null;
  } finally {
    if (benchmarkSilentAbortController === controller) benchmarkSilentAbortController = null;
  }
};

const calculateBenchmarkCorrection = async () => {
  try {
    const requestSeq = ++benchmarkRequestSeq;
    if (benchmarkRecalcTimer) {
      clearTimeout(benchmarkRecalcTimer);
      benchmarkRecalcTimer = null;
    }
    if (benchmarkSilentAbortController) {
      benchmarkSilentAbortController.abort();
      benchmarkSilentAbortController = null;
    }
    const analysis = await benchmarkCorrectionApiCall();
    if (requestSeq !== benchmarkRequestSeq) return null;
    applyBenchmarkAnalysisToForm(analysis);
    benchmarkInteractiveDirty.value = false;
    await loadValuationProcessDraft();
    showToast(
        analysis.complete ? '基准地价系数修正法测算已完成。' : '基准地价系数修正法已试算，仍有参数或因素待确认。',
      analysis.complete ? 'success' : 'warning'
    );
    return analysis;
  } catch (error) {
    showToast(`基准地价系数修正法计算失败：${error.message}`, 'error');
    return null;
  }
};

const scheduleBenchmarkRecalc = (delay = 450) => {
  benchmarkInteractiveDirty.value = true;
  persistBenchmarkAnalysisSnapshot({ dirty: true });
  if (benchmarkRecalcTimer) clearTimeout(benchmarkRecalcTimer);
  const requestSeq = ++benchmarkRequestSeq;
  benchmarkRecalcTimer = setTimeout(() => {
    benchmarkRecalcTimer = null;
    calculateBenchmarkCorrectionSilent(requestSeq);
  }, delay);
};

watch(
  () => [
    form.set_plot_ratio_display?.value,
    form.set_plot_ratio?.value,
    form.plot_ratio_display?.value,
    form.plot_ratio?.value,
    form.land_use_term_years?.value,
    form.land_use_term?.value,
    form.valuation_date?.value,
    form.land_development_set?.value,
    form.land_area?.value,
    form.land_area_mode?.value
  ],
  () => {
    if (activeTab.value !== 'p5' || activeProcessMethodKey.value !== 'benchmark_corr') return;
    syncBenchmarkLinkedParameters();
    persistBenchmarkAnalysisSnapshot({ dirty: true });
    scheduleBenchmarkRecalc(300);
  }
);

const flushBenchmarkRecalc = async () => {
  if (benchmarkRecalcTimer) {
    clearTimeout(benchmarkRecalcTimer);
    benchmarkRecalcTimer = null;
  }
  if (!benchmarkInteractiveDirty.value) return;
  await calculateBenchmarkCorrectionSilent();
  if (activeTab.value === 'p5') await loadValuationProcessDraft();
};

watch(benchmarkWorkspaceView, async (view) => {
  if (view !== 'narratives') return;
  if (activeTab.value !== 'p5' || activeProcessMethodKey.value !== 'benchmark_corr') return;
  await flushBenchmarkRecalc();
  await loadValuationProcessDraft();
});

// 选优劣度 → 查表自动取系数（区域/个别因素）
const onBenchmarkRegionalLevelChange = (factor) => {
  if (!factor) return;
  const selected = (factor.options || []).find(item => item.label === factor.level);
  factor.grade = factor.level || factor.grade || '';
  if (selected && selected.coefficient !== undefined && selected.coefficient !== null) {
    factor.coefficient = String(selected.coefficient);
    if (!String(factor.description || '').trim() && selected.indicator_desc !== undefined) {
      factor.description = selected.indicator_desc;
    }
  }
  scheduleBenchmarkRecalc();
};

const onBenchmarkIndividualLevelChange = (factor) => {
  if (!factor) return;
  const selected = (factor.options || []).find(item => item.label === factor.level);
  factor.grade = factor.level || factor.grade || '';
  if (selected && selected.coefficient !== undefined && selected.coefficient !== null) {
    factor.coefficient = String(selected.coefficient);
  }
  scheduleBenchmarkRecalc();
};

const benchmarkFactorDescriptionPlaceholder = (factor) => {
  const name = factor?.indicator || factor?.sub_factor || '该因素';
  const options = factor?.options || [];
  const general = options.find(item => item.label === '一般') || options[0] || {};
  const example = general.criteria || general.indicator_desc || '';
  return example ? `填写${name}实际情况，如：${example}` : `填写${name}实际情况`;
};

const onBenchmarkParameterInput = () => {
  syncBenchmarkLinkedParameters();
  scheduleBenchmarkRecalc();
};

const onBenchmarkFrontageWidthInput = () => {
  if (benchmarkUsesRoutePrice.value) {
    syncBenchmarkCommercialSplitFields();
  } else {
    syncBenchmarkFrontageDepth();
  }
  onBenchmarkParameterInput();
};

const onBenchmarkFrontageDepthInput = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.parameters.frontage_depth_m = benchmarkAnalysis.value.frontage_depth_m || '';
  benchmarkAnalysis.value.parameters.frontage_depth_source = benchmarkAnalysis.value.frontage_depth_m ? 'manual' : '';
  syncBenchmarkCommercialSplitFields();
  onBenchmarkParameterInput();
};

const onBenchmarkFrontageRelationChange = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.frontage_relation ||= 'adjacent';
  benchmarkAnalysis.value.parameters.frontage_relation = benchmarkAnalysis.value.frontage_relation;
  if (benchmarkAnalysis.value.frontage_relation !== 'setback') {
    benchmarkAnalysis.value.frontage_depth_m = '';
    benchmarkAnalysis.value.parameters.frontage_depth_m = '';
  }
  syncBenchmarkCommercialSplitFields();
  onBenchmarkParameterInput();
};

const onBenchmarkRoadGradeChange = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.route_road_grade = benchmarkAnalysis.value.parameters.route_road_grade || '';
  const matched = benchmarkRoadTypeFromGrade(benchmarkAnalysis.value.route_road_grade);
  if (matched) {
    benchmarkAnalysis.value.parameters.route_road_type = matched;
    benchmarkAnalysis.value.route_road_type = matched;
  }
  syncBenchmarkCommercialSplitFields();
  onBenchmarkParameterInput();
};

const onBenchmarkCornerChange = () => {
  benchmarkAnalysis.value.is_corner = benchmarkBoolValue(benchmarkAnalysis.value.is_corner);
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.parameters.is_corner = benchmarkAnalysis.value.is_corner;
  syncBenchmarkCornerFields();
  persistBenchmarkAnalysisSnapshot({ dirty: true });
  onBenchmarkParameterInput();
};

const onBenchmarkCornerPriceInput = () => {
  syncBenchmarkCornerFields();
  onBenchmarkParameterInput();
};

const clearBenchmarkCornerFields = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.is_corner = false;
  benchmarkAnalysis.value.parameters.is_corner = false;
  [
    'corner_route_price_a',
    'corner_route_price_b',
    'corner_main_route_price',
    'corner_side_route_price',
    'corner_price_ratio',
    'kc'
  ].forEach(key => {
    benchmarkAnalysis.value[key] = '';
    benchmarkAnalysis.value.parameters[key] = '';
  });
};

const clearBenchmarkCommercialRouteState = () => {
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.frontage_mode = 'non_street';
  benchmarkAnalysis.value.parameters.frontage_mode = 'non_street';
  benchmarkAnalysis.value.route_segment_id = '';
  benchmarkAnalysis.value.route_price = '';
  benchmarkAnalysis.value.route_price_source_note = '';
  benchmarkAnalysis.value.route_road_grade = '';
  benchmarkAnalysis.value.route_road_type = '';
  benchmarkAnalysis.value.ku_grade = '';
  [
    'route_segment_id',
    'route_price',
    'route_price_source',
    'route_price_source_note',
    'route_road_grade',
    'route_road_type',
    'ku_grade',
    'ku',
    'frontage_width_m',
    'frontage_depth_m',
    'frontage_relation',
    'commercial_area_m2',
    'frontage_standard_depth_m',
    'frontage_area_m2',
    'non_frontage_area_m2',
    'frontage_average_depth_m',
    'kd',
    'kk',
    'kc'
  ].forEach(key => {
    benchmarkAnalysis.value[key] = '';
    benchmarkAnalysis.value.parameters[key] = '';
  });
  clearBenchmarkCornerFields();
};

const onBenchmarkLandUseTypeChange = () => {
  ensureBenchmarkAnalysisDefaults();
  if (benchmarkAnalysis.value.land_use_type !== '商业服务业用地') {
    clearBenchmarkCommercialRouteState();
  } else {
    benchmarkAnalysis.value.frontage_mode ||= benchmarkAnalysis.value.parameters?.frontage_mode || 'non_street';
    benchmarkAnalysis.value.parameters.frontage_mode = benchmarkAnalysis.value.frontage_mode;
  }
  onBenchmarkParameterInput();
};

const onBenchmarkFrontageModeChange = () => {
  ensureBenchmarkAnalysisDefaults();
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.parameters.frontage_mode = benchmarkAnalysis.value.frontage_mode || 'non_street';
  if (!['street_route_price', 'route_price_plus_non_street'].includes(benchmarkAnalysis.value.frontage_mode)) {
    benchmarkAnalysis.value.route_segment_id = '';
    benchmarkAnalysis.value.parameters.route_segment_id = '';
    benchmarkAnalysis.value.parameters.route_price = '';
    benchmarkAnalysis.value.parameters.route_price_source = '';
    benchmarkAnalysis.value.parameters.route_road_type = '';
    benchmarkAnalysis.value.route_road_type = '';
    benchmarkAnalysis.value.frontage_depth_m = '';
    benchmarkAnalysis.value.parameters.frontage_depth_m = '';
    clearBenchmarkCornerFields();
    ['commercial_area_m2', 'frontage_standard_depth_m', 'frontage_area_m2', 'non_frontage_area_m2', 'frontage_average_depth_m'].forEach(key => {
      benchmarkAnalysis.value[key] = '';
      benchmarkAnalysis.value.parameters[key] = '';
    });
  } else {
    syncBenchmarkCommercialSplitFields();
  }
  persistBenchmarkAnalysisSnapshot({ dirty: true });
  onBenchmarkParameterInput();
};

const onBenchmarkRouteSegmentChange = () => {
  ensureBenchmarkAnalysisDefaults();
  const selected = benchmarkSelectedRouteSegment.value;
  benchmarkAnalysis.value.parameters ||= {};
  benchmarkAnalysis.value.parameters.route_segment_id = benchmarkAnalysis.value.route_segment_id || '';
  if (selected) {
    benchmarkAnalysis.value.parameters.route_price = selected.route_price || '';
    benchmarkAnalysis.value.parameters.route_road_type = selected.road_type || '';
    benchmarkAnalysis.value.parameters.route_road_grade = selected.road_type || '';
    benchmarkAnalysis.value.route_road_grade = benchmarkAnalysis.value.parameters.route_road_grade;
    benchmarkAnalysis.value.parameters.frontage_standard_depth_m = selected.standard_depth || benchmarkDefaultStandardDepth(selected.road_type) || '';
    benchmarkAnalysis.value.frontage_standard_depth_m = benchmarkAnalysis.value.parameters.frontage_standard_depth_m;
    benchmarkAnalysis.value.parameters.route_price_source = 'route_table';
    if (!String(benchmarkAnalysis.value.parameters.route_price_source_note || '').trim()) {
      benchmarkAnalysis.value.parameters.route_price_source_note = `${selected.road_name}${selected.route_start || selected.route_end ? `（${selected.route_start || ''}至${selected.route_end || ''}）` : ''}路线价段`;
    }
  } else {
    benchmarkAnalysis.value.parameters.route_road_type = '';
    benchmarkAnalysis.value.route_road_type = '';
  }
  benchmarkAnalysis.value.route_price = benchmarkAnalysis.value.parameters.route_price || '';
  benchmarkAnalysis.value.route_road_type = benchmarkAnalysis.value.parameters.route_road_type || '';
  benchmarkAnalysis.value.route_price_source_note = benchmarkAnalysis.value.parameters.route_price_source_note || '';
  syncBenchmarkCommercialSplitFields();
  persistBenchmarkAnalysisSnapshot({ dirty: true });
  onBenchmarkParameterInput();
};

const onBenchmarkKuChange = () => {
  ensureBenchmarkAnalysisDefaults();
  const selected = benchmarkKuOptions.value.find(item => item.label === benchmarkAnalysis.value.ku_grade || item.grade === benchmarkAnalysis.value.ku_grade);
  benchmarkAnalysis.value.individual_factors ||= {};
  benchmarkAnalysis.value.individual_factors.surrounding_land_use ||= {};
  benchmarkAnalysis.value.individual_factors.surrounding_land_use.grade = benchmarkAnalysis.value.ku_grade || '';
  benchmarkAnalysis.value.individual_factors.surrounding_land_use.level = benchmarkAnalysis.value.ku_grade || '';
  if (selected?.coefficient !== undefined) {
    benchmarkAnalysis.value.individual_factors.surrounding_land_use.coefficient = String(selected.coefficient);
  }
  onBenchmarkParameterInput();
};

const onBenchmarkCoverageScopeChange = () => {
  if (benchmarkAnalysis.value.coverage_scope !== '乡镇') {
    benchmarkAnalysis.value.township_grade = '';
  } else {
    benchmarkAnalysis.value.township_grade ||= benchmarkTownshipGradeOptions.value[0] || '';
  }
  onBenchmarkParameterInput();
};

const onBenchmarkMapIdsChange = () => {
  ensureBenchmarkAnalysisDefaults();
  persistBenchmarkAnalysisSnapshot({ dirty: true });
};

const benchmarkRegionalSum = computed(() => {
  const list = benchmarkAnalysis.value?.regional_factors || [];
  let sum = 0;
  let any = false;
  for (const factor of list) {
    const n = numericValue(factor?.coefficient);
    if (Number.isFinite(n)) { sum += n; any = true; }
  }
  return any ? sum.toFixed(4) : '';
});

const BENCHMARK_INDIVIDUAL_FACTOR_LABELS = {
  area: '宗地面积修正（Ks）',
  shape: '宗地形状修正（Ka）',
  landscape: '景观环境修正（Ke）',
  orientation: '建筑物朝向修正（Kto）'
};
const benchmarkIndividualFactorRows = computed(() => {
  const factors = benchmarkAnalysis.value?.individual_factors || {};
  const rows = [];
  for (const fkey of ['area', 'shape', 'landscape', 'orientation']) {
    const data = factors[fkey];
    if (data && typeof data === 'object') {
      rows.push({ key: fkey, label: BENCHMARK_INDIVIDUAL_FACTOR_LABELS[fkey] || fkey, data });
    }
  }
  return rows;
});

const applyIncomeFactorLevel = (factor, slot) => {
  const selected = (factor.levels || []).find(item => item.label === factor.cases?.[slot]?.level_label);
  if (!selected) return;
  factor.cases[slot].value = selected.value || selected.label;
  factor.cases[slot].source = factor.key === 'transaction_condition' && factor.cases[slot].value === '正常交易'
    ? 'system_default'
    : 'manual_override';
  if (factor.key === 'transaction_condition' && factor.cases[slot].value === '正常交易') {
    factor.cases[slot].override_reason = '';
  }
  recalculateIncomeFactorCase(factor, slot);
};

const applyIncomeSubjectLevel = (factor) => {
  const selected = (factor.levels || []).find(item => item.label === factor.subject_level_label);
  if (selected) factor.subject_value = selected.value || selected.label;
  comparableSlots.forEach(slot => recalculateIncomeFactorCase(factor, slot));
};

const incomeFactorCoefficient = (factor, slot) => {
  const subjectIndex = numericValue(factor?.subject_index || 100);
  const caseIndex = numericValue(factor?.cases?.[slot]?.index);
  if (!Number.isFinite(subjectIndex) || !Number.isFinite(caseIndex) || subjectIndex <= 0 || caseIndex <= 0) return '';
  return (subjectIndex / caseIndex).toFixed(4);
};

const incomeFactorSourceLabel = (source) => ({
  rent_instance: '实例引用',
  system_default: '系统默认',
  manual_override: '人工调整',
  manual: '人工填写'
}[source] || '人工填写');

const incomeFactorCaseStatus = (factor, slot) => {
  const coefficient = incomeFactorCoefficient(factor, slot);
  if (!coefficient) return '指数待校核';
  return Math.abs(Number(coefficient) - 1) < 0.00005 ? '无需修正' : `修正系数 ${coefficient}`;
};

const incomeFactorCaseStatusClass = (factor, slot) => ({
  'factor-status-chip': true,
  'status-confirmed': factor?.cases?.[slot]?.confirmed,
  'status-adjusted': incomeFactorCoefficient(factor, slot) && Math.abs(Number(incomeFactorCoefficient(factor, slot)) - 1) >= 0.00005,
  'status-pending': !factor?.cases?.[slot]?.confirmed
});

const markIncomeFactorSubjectEdited = (factor) => {
  comparableSlots.forEach(slot => {
    if (factor?.cases?.[slot]) factor.cases[slot].confirmed = false;
  });
};

const confirmIncomeFactor = (factor) => {
  comparableSlots.forEach(slot => {
    if (factor.cases?.[slot] && String(factor.cases[slot].index || '').trim()) {
      factor.cases[slot].confirmed = true;
    }
  });
};

const isFactorConfirmed = (factor) => {
  return comparableSlots.every(slot => {
    const caseItem = factor.cases?.[slot];
    if (!caseItem) return false;
    return String(caseItem.index || '').trim() && caseItem.confirmed === true;
  });
};

const toggleFactorConfirm = (factor) => {
  const isConfirmed = isFactorConfirmed(factor);
  comparableSlots.forEach(slot => {
    if (factor.cases?.[slot]) {
      if (isConfirmed) {
        factor.cases[slot].confirmed = false;
      } else if (String(factor.cases[slot].index || '').trim()) {
        factor.cases[slot].confirmed = true;
      }
    }
  });
  if (!isConfirmed) {
    factor.tempExpanded = false;
  }
};

const confirmAllIncomeFactors = () => {
  (incomeAnalysis.value?.rent_factor_items || []).forEach(confirmIncomeFactor);
};

const cancelAllIncomeFactors = () => {
  (incomeAnalysis.value?.rent_factor_items || []).forEach(factor => {
    comparableSlots.forEach(slot => {
      if (factor.cases?.[slot]) {
        factor.cases[slot].confirmed = false;
      }
    });
    factor.tempExpanded = false;
  });
};

const confirmIncomeCapRates = () => {
  incomeAnalysis.value.cap_rate_parameters ||= {};
  incomeAnalysis.value.cap_rate_parameters.confirmed = true;
};

const triggerIncomeImageUpload = (index, kind) => {
  const el = document.getElementById(`income-file-${index}-${kind}`);
  if (el) el.click();
};

const removeIncomeImage = (index, kind) => {
  const item = incomeAnalysis.value.rent_instances?.[index];
  if (!item) return;
  if (kind === 'photo') {
    item.photo_data = '';
    item.photo_name = '';
  } else {
    item.location_image_data = '';
    item.location_image_name = '';
  }
  form.income_cap_analysis.value = JSON.parse(JSON.stringify(incomeAnalysis.value));
};

const handleIncomeImageUpload = (index, kind, event) => {
  const file = event.target.files?.[0];
  event.target.value = '';
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const item = incomeAnalysis.value.rent_instances?.[index];
    if (!item) return;
    if (kind === 'photo') {
      item.photo_data = reader.result;
      item.photo_name = file.name;
    } else {
      item.location_image_data = reader.result;
      item.location_image_name = file.name;
    }
    form.income_cap_analysis.value = JSON.parse(JSON.stringify(incomeAnalysis.value));
  };
  reader.readAsDataURL(file);
};

const addCostLocationFactor = () => {
  if (!costAnalysis.value.location_factors) costAnalysis.value.location_factors = [];
  const targetGroup = costNewLocationFactorGroup.value || costLocationFactorGroups.value[0] || '区域及个别因素';
  const newFactor = {
    key: `manual_location_${Date.now()}`,
    usage_key: costAnalysis.value.usage_scenarios?.[0]?.key || '',
    group: targetGroup,
    label: '待填写因素',
    description: '',
    level: '一般',
    levels: ['优', '较优', '一般', '较劣', '劣'],
    grade_amplitude: '1',
    weight: '',
    correction_rate: '0',
    source: 'manual',
    confirmed: false
  };
  const factors = costAnalysis.value.location_factors;
  let insertAt = -1;
  for (let i = 0; i < factors.length; i += 1) {
    if (String(factors[i].group || '') === String(targetGroup)) insertAt = i;
  }
  if (insertAt === -1) {
    factors.push(newFactor);
  } else {
    factors.splice(insertAt + 1, 0, newFactor);
  }
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const isManualCostLocationFactor = (factor) => (
  String(factor?.source || '').includes('manual') || String(factor?.key || '').startsWith('manual_location_')
);

const removeCostLocationFactor = (factor, index) => {
  if (!costAnalysis.value?.location_factors) return;
  if (isManualCostLocationFactor(factor)) {
    costAnalysis.value.location_factors.splice(index, 1);
  } else {
    factor.enabled = false;
    factor.confirmed = false;
  }
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const restoreCostLocationFactor = (factor) => {
  if (!factor) return;
  factor.enabled = true;
  factor.confirmed = false;
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const restoreCostLocationFactors = () => {
  (costAnalysis.value?.location_factors || []).forEach((factor) => {
    if (factor?.enabled === false && !isManualCostLocationFactor(factor)) {
      factor.enabled = true;
      factor.confirmed = false;
    }
  });
  recalculateLocalLocationResults();
  scheduleCostInteractiveRecalc();
};

const addCostRiskItem = () => {
  if (!costAnalysis.value.risk_items) costAnalysis.value.risk_items = [];
  costAnalysis.value.risk_items.push({
    usage_key: costAnalysis.value.usage_scenarios?.[0]?.key || '',
    group: '市场风险',
    label: '待填写风险因素',
    weight: '',
    level: '',
    adjustment_rate: '',
    level_options: costRiskLevelOptions({}),
    confirmed: false
  });
};

const loadValuationProcessDraft = async () => {
  try {
    if (form.use_benchmark_corr?.value) {
      form.benchmark_corr_analysis.value = buildBenchmarkAnalysisPayload();
    }
    const draft = await apiJson('/api/build-valuation-process-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: buildFlatPayload(), overwrite: false })
    });
    valuationProcessDraft.methods = draft.methods || [];
    if (!valuationProcessDraft.methods.some(item => item.method_key === activeProcessMethodKey.value)) {
      activeProcessMethodKey.value = valuationProcessDraft.methods[0]?.method_key || '';
    }
    syncProcessNarrativesToForm(draft);
  } catch (error) {
    showToast(`估价过程草稿生成失败：${error.message}`, 'error');
  }
};

const openValuationProcess = async () => {
  activeTab.value = 'p5';
  if (form.cost_approx_analysis.value) {
    applyCostAnalysisToForm(form.cost_approx_analysis.value);
  }
  if (!marketAnalysis.value && form.market_comp_analysis.value) {
    applyMarketAnalysisToForm(JSON.parse(JSON.stringify(form.market_comp_analysis.value)));
  }
  if (form.income_cap_analysis.value) {
    applyIncomeAnalysisToForm(form.income_cap_analysis.value);
  }
  if (form.benchmark_corr_analysis.value) {
    applyBenchmarkAnalysisToForm(form.benchmark_corr_analysis.value);
  }
  await loadValuationProcessDraft();
  if (form.use_cost_approx.value && !(costAnalysis.value?.acquisition_items || []).length) {
    await calculateCostApproximation();
  }
  if (form.use_income_cap.value && !(incomeAnalysis.value?.rent_instances || []).length) {
    await calculateIncomeCapitalization();
  }
  if (form.use_benchmark_corr.value && !(benchmarkAnalysis.value?.regional_factors || []).length) {
    await calculateBenchmarkCorrection();
  }
};

const openCurrentMarketAnalysis = async (view = 'instances') => {
  activeTab.value = 'p5';
  if (!marketAnalysis.value && form.market_comp_analysis.value) {
    applyMarketAnalysisToForm(JSON.parse(JSON.stringify(form.market_comp_analysis.value)));
  }
  activeProcessMethodKey.value = 'market_comp';
  marketWorkspaceView.value = view;
  await loadValuationProcessDraft();
  if (!valuationProcessDraft.methods.some(item => item.method_key === 'market_comp')) {
    showToast('第四部分尚未采用市场比较法，当前报告分析未显示。', 'warning');
  }
};

const openComparableLibrary = async () => {
  activeTab.value = 'p6';
  comparableView.value = 'library';
  await initializeComparableLibrary();
};

const openRuleManagement = async () => {
  activeTab.value = 'p6';
  comparableView.value = 'schemes';
  await initializeComparableLibrary();
  await loadFactorScheme();
};

const warningTarget = (warning) => {
  if (warning?.target) return warning.target;
  const message = String(warning?.message || '');
  if (message.includes('成交公告证据') || message.includes('成交公告截图') || message.includes('位置图') || message.includes('现状图')) return 'evidence';
  if (message.includes('价格可比基础') || message.includes('最终正文')) return 'narratives';
  if (message.includes('规则') || message.includes('等级与建议指数')) return 'rules';
  if (message.includes('尚未确认') || message.includes('修正幅度') || message.includes('比准价格差异')) return 'factors';
  if (message.includes('实例') || message.includes('交易时间') || message.includes('土地用途')) return 'instances';
  if (message.includes('区片') || message.includes('政策')) return 'cost_policy';
  if (message.includes('土地取得费') || message.includes('相关税费') || message.includes('土地开发费')) return 'cost_items';
  if (message.includes('用途场景') || message.includes('区位修正')) return 'cost_scenarios';
  if (message.includes('租金实例') || message.includes('照片') || message.includes('位置图')) return 'income_instances';
  if (message.includes('收益还原法') && message.includes('因素')) return 'income_factors';
  if (message.includes('还原率') || message.includes('建筑面积') || message.includes('土地面积')) return 'income_parameters';
  return '';
};

const warningActionLabel = (warning) => {
  const target = warningTarget(warning);
  if (String(target).startsWith('benchmark_corr_analysis.')) return '基准地价校核';
  return ({
    evidence: '上传证据截图',
    rules: '规则管理',
    factors: '因素确认',
    instances: '实例与参数',
    narratives: '最终正文',
    library: '比较实例库',
    cost_policy: '政策与征收地类',
    cost_items: '费用测算',
    cost_scenarios: '年期与区位修正',
    cost_location: '年期与区位修正',
    income_instances: '房屋与租金实例',
    income_factors: '租金因素确认',
    income_parameters: '收入费用与还原率',
    valuation_date: '估价期日'
  }[target] || '');
};

const handleWarningAction = async (warning) => {
  const target = warningTarget(warning);
  if (String(target).startsWith('benchmark_corr_analysis.')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'benchmark_corr';
    revealWorkspaceForField(target);
    await loadValuationProcessDraft();
    await nextTick();
    focusProcessSource(target);
    return;
  }
  if (target === 'valuation_date') {
    scrollToField('valuation_date');
    return;
  }
  if (String(target).startsWith('income_')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'income_cap';
    incomeWorkspaceView.value = target === 'income_instances' ? 'instances' : target === 'income_factors' ? 'factors' : 'parameters';
    await loadValuationProcessDraft();
    return;
  }
  if (String(target).startsWith('cost_')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'cost_approx';
    costWorkspaceView.value = target === 'cost_policy' ? 'policy' : target === 'cost_items' ? 'costs' : 'adjustments';
    await loadValuationProcessDraft();
    return;
  }
  if (target === 'rules') {
    await openRuleManagement();
    return;
  }
  if (target === 'library') {
    await openComparableLibrary();
    return;
  }
  await openCurrentMarketAnalysis(
    target === 'evidence' || target === 'instances'
      ? 'instances'
      : target === 'narratives' ? 'narratives' : 'factors'
  );
  await nextTick();
  if (target === 'evidence') {
    document.getElementById('market-evidence-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  if (target === 'factors' && warning?.factor_key) {
    const factor = (marketAnalysis.value?.factors || []).find(item => item.key === warning.factor_key);
    if (factor) openFactorGuide(factor);
  }
};

const processAnalysisBinding = (section) => {
  const key = section?.key || '';
  if (key.startsWith('income_cap_')) {
    return {
      formKey: 'income_cap_analysis',
      current: incomeAnalysis.value,
      apply: (analysis) => { incomeAnalysis.value = analysis; }
    };
  }
  if (key.startsWith('cost_approx_')) {
    return {
      formKey: 'cost_approx_analysis',
      current: costAnalysis.value,
      apply: (analysis) => { costAnalysis.value = analysis; }
    };
  }
  if (key.startsWith('benchmark_corr_')) {
    return {
      formKey: 'benchmark_corr_analysis',
      current: benchmarkAnalysis.value,
      apply: (analysis) => { benchmarkAnalysis.value = analysis; }
    };
  }
  return {
    formKey: 'market_comp_analysis',
    current: marketAnalysis.value,
    apply: (analysis) => { marketAnalysis.value = analysis; }
  };
};

const saveProcessNarrativeOverride = async (section) => {
  const binding = processAnalysisBinding(section);
  const analysis = JSON.parse(JSON.stringify(form[binding.formKey]?.value || binding.current || {}));
  analysis.narrative_overrides ||= {};
  analysis.narrative_overrides[section.key] = section.effective_text || '';
  form[binding.formKey].value = analysis;
  binding.apply(analysis);
  section.override_text = section.effective_text || '';
  if (form[section.key]) {
    form[section.key].value = section.effective_text || '';
    form[section.key].origin = 'manual';
    form[section.key].is_dirty = true;
  }
  await loadValuationProcessDraft();
  showToast('人工正文覆盖已保存，重新计算不会覆盖该段。');
};

const restoreProcessNarrative = async (section) => {
  const binding = processAnalysisBinding(section);
  const analysis = JSON.parse(JSON.stringify(form[binding.formKey]?.value || binding.current || {}));
  analysis.narrative_overrides ||= {};
  delete analysis.narrative_overrides[section.key];
  form[binding.formKey].value = analysis;
  binding.apply(analysis);
  await loadValuationProcessDraft();
  showToast('已恢复系统草稿。');
};

const openProcessSource = async (target) => {
  if (String(target).startsWith('benchmark_')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'benchmark_corr';
    const text = String(target);
    if (text.includes('_ki') || text.includes('region')) benchmarkWorkspaceView.value = 'factors';
    else if (
      text.includes('_kv')
      || text.includes('_ky')
      || text.includes('_kt')
      || text.includes('_ks')
      || text.includes('_ka')
      || text.includes('_ke')
      || text.includes('_kto')
      || text.includes('_kf')
      || text.includes('plot_ratio')
      || text.includes('cap_rate')
      || text.includes('ku')
      || text.includes('frontage')
      || text.includes('corner')
      || text.includes('_kd')
      || text.includes('_kk')
      || text.includes('_kc')
    ) benchmarkWorkspaceView.value = 'corrections';
    else benchmarkWorkspaceView.value = 'base';
    await loadValuationProcessDraft();
    await nextTick();
    const id = benchmarkWorkspaceView.value === 'factors'
      ? 'focus_item_benchmark_corr_analysis_regional'
      : benchmarkWorkspaceView.value === 'corrections'
        ? 'focus_item_benchmark_corr_analysis_corrections'
        : 'focus_item_benchmark_corr_analysis';
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  if (String(target).startsWith('income_')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'income_cap';
    incomeWorkspaceView.value = target === 'income_instances' ? 'instances' : target === 'income_factors' ? 'factors' : 'parameters';
    await loadValuationProcessDraft();
    return;
  }
  if (String(target).startsWith('cost')) {
    activeTab.value = 'p5';
    activeProcessMethodKey.value = 'cost_approx';
    costWorkspaceView.value = target === 'cost_adjustments' ? 'adjustments' : target === 'cost_policy' ? 'policy' : 'costs';
    await loadValuationProcessDraft();
    return;
  }
  if (target === 'library') {
    await openComparableLibrary();
    await nextTick();
    document.getElementById('comparable-library-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  await openCurrentMarketAnalysis('factors');
};

const focusProcessSource = (key) => {
  if (String(key).includes('.')) {
    focusNestedProcessField(key);
    return;
  }
  if (key.startsWith('income_cap_')) {
    openProcessSource('income_parameters');
    return;
  }
  if (key.startsWith('market_comp_')) {
    openProcessSource(key === 'market_comp_analysis' ? 'factors' : 'library');
    return;
  }
  scrollToField(key);
};

const buildDraftPayload = () => {
  const payload = buildFlatPayload();
  // 智能拉齐：在草稿计算生成时，将5个确价大段落要素字段在入参时置空，以规避后端 _should_assign 对非强刷增量同步的阻断，
  // 从而让后端随时返回最新生成的文本，交由前端 UI 的脏数据守卫（is_dirty）做精细的覆盖与更新决策
  ['valuation_method_reasons', 'valuation_method_applicability', 'final_price_determination', 'valuation_result_statement', 'infrastructure_detail', 'formula_display_text', 'cost_approx_land_class_intro', 'cost_approx_process_intro'].forEach(key => {
    payload[key] = '';
  });
  if (!form.requires_manual_final_price.value) {
    ['final_unit_price', 'final_total_price', 'final_total_price_upper'].forEach(key => {
      payload[key] = '';
    });
  }
  return payload;
};

const buildOwnershipDraftPayload = () => {
  const payload = buildFlatPayload();
  ['land_registration_desc', 'land_right_desc', 'land_use_status_desc'].forEach(key => {
    const field = form[key];
    const value = String(field?.value || '');
    if (!field?.is_dirty || value.includes('______') || value.includes('【请填写')) {
      payload[key] = '';
    }
  });
  return payload;
};

const setGeneratedField = (key, value, force = false) => {
  const field = form[key];
  if (!field) return;
  if (value === undefined || value === null) return;
  
  const current_val = String(field.value || '');
  // 检测当前大文本框中的旧草稿是否是“急需更新的失效草稿”（包含下划线、请填写，或空置时退化生成的稳妥概括句）
  const isStaleDraft = current_val.includes('______') || 
                       current_val.includes('【请填写') ||
                       current_val.includes('未在本段写入未经核定') ||
                       current_val.includes('不写入未经核定') ||
                       current_val.includes('未录入完整基准地价');
                       
  const canUpdate = force || 
                    !field.is_dirty && (field.origin === 'generated' || !current_val.trim()) ||
                    isStaleDraft;
                    
  if (canUpdate) {
    field.value = value;
    field.origin = 'generated';
    field.is_dirty = false;
  }
};

const updateValuationSegments = (drafts) => {
  valuation_method_reasons_segments.value = drafts.valuation_method_reasons_segments || [];
  valuation_method_applicability_segments.value = drafts.valuation_method_applicability_segments || [];
  final_price_determination_segments.value = drafts.final_price_determination_segments || [];
  valuation_result_statement_segments.value = drafts.valuation_result_statement_segments || [];
  infrastructure_detail_segments.value = drafts.infrastructure_detail_segments || [];
  formula_display_text_segments.value = drafts.formula_display_text_segments || [];
};

const regenerateValuationNarratives = async (force = false) => {
  if (!selectedValuationMethods.value.length) {
    showToast('请先勾选至少一种评估方法。', 'warning');
    return;
  }
  const edited = ['formula_display_text', 'valuation_method_reasons', 'valuation_method_applicability', 'final_price_determination', 'valuation_result_statement', 'infrastructure_detail', 'cost_approx_land_class_intro', 'cost_approx_process_intro']
    .some(key => form[key]?.is_dirty && String(form[key]?.value || '').trim());
  if (force && edited && !confirm('当前确价正文已有手工修改，是否覆盖为系统重新生成的草稿？')) {
    return;
  }

  if (force) {
    method_warning_acknowledged.value = {};
  }

  try {
    const res = await fetch('/api/build-valuation-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: buildDraftPayload(), overwrite: force })
    });
    if (!res.ok) throw new Error('生成确价草稿失败');
    const result = await res.json();
    if (result.status === 'success') {
      const drafts = result.data;
      ['formula_display_text', 'valuation_basis_docs_rendered', 'valuation_method_reasons', 'valuation_method_applicability', 'final_price_determination', 'valuation_result_statement', 'infrastructure_detail', 'cost_approx_land_class_intro', 'cost_approx_process_intro', 'final_unit_price', 'final_total_price', 'final_total_price_upper', 'requires_manual_final_price'].forEach(key => {
        setGeneratedField(key, drafts[key], force);
      });
      updateValuationSegments(drafts);
      
      // 更新背景证据链预警
      method_warnings.value = drafts.method_warnings || [];

      const warnings = drafts.valuation_warnings || [];
      if (warnings.length) {
        showToast(`确价草稿已生成，但需复核：${warnings[0]}`, 'warning');
      } else {
        showToast('确价测算段落与智能引用热区已更新。');
      }
    }
  } catch (err) {
    showToast('调用后端确价引擎失败: ' + err.message, 'error');
  }
};

const updateMethodWarnings = async () => {
  try {
    const res = await fetch('/api/build-valuation-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: buildDraftPayload(), overwrite: false })
    });
    if (!res.ok) return;
    const result = await res.json();
    if (result.status === 'success') {
      method_warnings.value = result.data.method_warnings || [];
    }
  } catch (err) {
    console.error('静默更新证据预警失败:', err);
  }
};

const acknowledgeWarning = (key) => {
  method_warning_acknowledged.value[key] = true;
  showToast('已确认该条方法适用性预警。', 'success');
};

const syncValuationSegments = async () => {
  try {
    const res = await fetch('/api/build-valuation-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: buildDraftPayload(), overwrite: false })
    });
    if (!res.ok) throw new Error('同步确价分词失败');
    const result = await res.json();
    if (result.status === 'success') {
      updateValuationSegments(result.data);
      showToast('确价热区已同步。');
    }
  } catch (err) {
    showToast('同步确价热区失败: ' + err.message, 'error');
  }
};

const regenerateOwnershipDraft = async (force = false) => {
  const edited = ['land_registration_desc', 'land_right_desc', 'land_use_status_desc']
    .some(key => form[key]?.is_dirty && String(form[key]?.value || '').trim());
  if (force && edited && !confirm('当前权属正文已有手工修改，是否覆盖为系统重新生成的草稿？')) {
    return;
  }
  
  const payload = buildOwnershipDraftPayload();
  
  try {
    const res = await fetch('/api/build-ownership-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload, overwrite: force })
    });
    if (!res.ok) throw new Error('生成草稿失败');
    const result = await res.json();
    if (result.status === 'success') {
      const drafts = result.data;
      if (drafts.ownership_scenario_type) form.ownership_scenario_type.value = drafts.ownership_scenario_type;
      if (drafts.ownership_scenario_type) form.land_status_type.value = drafts.ownership_scenario_type === 'registered_complete' ? 'registered' : drafts.ownership_scenario_type;
      if (drafts.asset_use_category) form.asset_use_category.value = drafts.asset_use_category;
      
      const keysToUpdate = ['land_registration_desc', 'land_right_desc', 'land_use_status_desc', 'basis_docs_rendered', 'basis_docs_phrase'];
      keysToUpdate.forEach(key => setGeneratedField(key, drafts[key], force));
      
      // 智能依据反填脏守卫：仅在不强刷且前端清单为空、且未人工编辑时，才自动反填后端推导出的现有依据
      if (drafts.basis_docs_list && form.basis_docs_list) {
        const docListField = form.basis_docs_list;
        const currentVal = String(docListField.value || '').trim();
        const canFillDocs = force || !currentVal || (!docListField.is_dirty && docListField.origin === 'generated');
        if (canFillDocs) {
          docListField.value = drafts.basis_docs_list;
          docListField.origin = 'generated';
          docListField.is_dirty = false;
        }
      }
      
      // 更新伴生的 Segments 片段数组响应式 ref，供热区透视
      land_registration_desc_segments.value = drafts.land_registration_desc_segments || [];
      land_right_desc_segments.value = drafts.land_right_desc_segments || [];
      land_use_status_desc_segments.value = drafts.land_use_status_desc_segments || [];

      showToast('权属草稿与智能引用热区已更新', 'success');
    }
  } catch (err) {
    showToast('调用后端草稿引擎失败: ' + err.message, 'error');
  }
};

const syncPerspectiveSegments = async () => {
  const payload = buildOwnershipDraftPayload();
  
  try {
    const res = await fetch('/api/build-ownership-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: payload, overwrite: false })
    });
    if (!res.ok) throw new Error('同步分词失败');
    const result = await res.json();
    if (result.status === 'success') {
      const drafts = result.data;
      
      // 智能脏数据升级同步：若后端已将其重组升级为新版条目化清单（含 '1. ' ），且前端仍是老版长段落，则自动回写更新
      const keysToSync = ['land_registration_desc', 'land_right_desc', 'land_use_status_desc'];
      keysToSync.forEach(key => {
        const field = form[key];
        if (field) {
          const currentVal = String(field.value || '').trim();
          const newVal = String(drafts[key] || '').trim();
          if (newVal && newVal.includes('1. ') && !currentVal.includes('1. ')) {
            field.value = newVal;
            field.origin = 'generated';
            field.is_dirty = false;
          }
        }
      });

      land_registration_desc_segments.value = drafts.land_registration_desc_segments || [];
      land_right_desc_segments.value = drafts.land_right_desc_segments || [];
      land_use_status_desc_segments.value = drafts.land_use_status_desc_segments || [];
    }
  } catch (err) {
    console.error('静默同步分词 Segments 失败:', err);
  }
};

const togglePerspective = () => {
  showPerspective.value = !showPerspective.value;
  if (showPerspective.value) {
    syncPerspectiveSegments();
  }
};

const toggleValuationPerspective = () => {
  showValuationPerspective.value = !showValuationPerspective.value;
  if (showValuationPerspective.value) {
    syncValuationSegments();
  }
};

const onOwnershipControlChange = (key) => {
  onFieldInput(key);
  regenerateOwnershipDraft(true);
};

// 💡 V6.2 伴生气泡悬浮 Tooltip 状态与触发机制
const tooltipState = reactive({
  show: false,
  x: 0,
  y: 0,
  title: '',
  field: ''
});

const showRefTooltip = (seg, event) => {
  const targetField = seg.field || (seg.fields && seg.fields[0]);
  if (!targetField) return;
  const reg = FIELD_REGISTRY[targetField];
  
  const rect = event.target.getBoundingClientRect();
  tooltipState.x = rect.left + rect.width / 2;
  tooltipState.y = rect.top + window.scrollY;
  tooltipState.title = `📌 引用字段：${reg?.label || targetField}`;
  tooltipState.field = targetField;
  tooltipState.show = true;
};

const hideRefTooltip = () => {
  tooltipState.show = false;
};

const activeFlickerField = ref('');
let activeFlickerTimer = null;

let activeFlickerDomEl = null;
const clearActiveFlickerDom = () => {
  if (activeFlickerDomEl) {
    activeFlickerDomEl.classList.remove('flicker-glow-active-dom');
    activeFlickerDomEl = null;
  }
};

const resolveFlickerDomElement = (targetField) => {
  const field = String(targetField || '');
  if (!field) return null;
  return (
    document.getElementById(`focus_item_${sourceKeyFragment(field)}`)
    || document.getElementById(`focus_item_${field}`)
    || document.getElementById(`focus_item_${field.split('.')[0]}`)
  );
};

const triggerFieldHighlight = (targetField, duration = 2500) => {
  activeFlickerField.value = '';
  if (activeFlickerTimer) clearTimeout(activeFlickerTimer);
  clearActiveFlickerDom();
  nextTick(() => {
    activeFlickerField.value = targetField;
    // i4：部分容器（如 land_location_full）未绑定 flicker class；
    // 直接给命中的 focus_item_* DOM 加闪烁类，确保热区跳转一定高亮。
    const el = resolveFlickerDomElement(targetField);
    if (el) {
      const target = el.querySelector?.('.field-input, input, select, textarea') || el;
      target.classList.add('flicker-glow-active-dom');
      activeFlickerDomEl = target;
    }
    activeFlickerTimer = setTimeout(() => {
      if (activeFlickerField.value === targetField) {
        activeFlickerField.value = '';
      }
      clearActiveFlickerDom();
    }, duration);
  });
};

const revealFieldElement = (el) => {
  let details = el?.closest?.('details');
  while (details) {
    details.open = true;
    details = details.parentElement?.closest?.('details');
  }
};

const revealWorkspaceForField = (targetField) => {
  if (String(targetField).startsWith('income_cap_analysis.')) {
    activeProcessMethodKey.value = 'income_cap';
    if (targetField.includes('.rent_factor_items.')) incomeWorkspaceView.value = 'factors';
    else if (
      targetField.includes('.income_parameters.')
      || targetField.includes('.expense_parameters.')
      || targetField.includes('.cap_rate_parameters.')
      || targetField.includes('.income_results.')
    ) incomeWorkspaceView.value = 'parameters';
    else incomeWorkspaceView.value = 'instances';
    return;
  }
  if (String(targetField).startsWith('market_comp_analysis.')) {
    activeProcessMethodKey.value = 'market_comp';
    marketWorkspaceView.value = (
      targetField.includes('.factors.')
      || targetField.includes('.monthly_growth_rate')
      || targetField.includes('.land_reduction_rate')
    ) ? 'factors' : 'instances';
    return;
  }
  if (String(targetField).startsWith('cost_approx_analysis.')) {
    activeProcessMethodKey.value = 'cost_approx';
    if (
      targetField.includes('.compensation_zone')
      || targetField.includes('.policy_basis')
      || targetField.includes('.policy_documents.')
      || targetField.includes('.cost_basis_attachment_inventory')
      || targetField.includes('.green_seedling')
    ) {
      costWorkspaceView.value = 'policy';
    } else if (
      targetField.includes('.location')
      || targetField.includes('.risk')
      || targetField.includes('.usage')
      || targetField.includes('.development_cycle_years')
      || targetField.includes('.interest_rate')
      || targetField.includes('.usage_results')
    ) {
      costWorkspaceView.value = 'adjustments';
    } else {
      costWorkspaceView.value = 'costs';
    }
    return;
  }
  if (String(targetField).startsWith('benchmark_corr_analysis.')) {
    activeProcessMethodKey.value = 'benchmark_corr';
    if (
      targetField.includes('.regional_factors')
      || targetField.includes('.sum_ki')
    ) {
      benchmarkWorkspaceView.value = 'factors';
    } else if (
      targetField.includes('.individual_factors')
      || targetField.includes('.plot_ratio')
      || targetField.includes('.kv')
      || targetField.includes('.ky')
      || targetField.includes('.kt')
      || targetField.includes('.kf')
      || targetField.includes('.cap_rate')
      || targetField.includes('.term_years')
      || targetField.includes('_date')
      || targetField.includes('.months_elapsed')
      || targetField.includes('.monthly_growth_rate')
      || targetField.includes('.ku')
      || targetField.includes('.frontage')
      || targetField.includes('.corner')
      || targetField.includes('.kd')
      || targetField.includes('.kk')
      || targetField.includes('.kc')
    ) {
      benchmarkWorkspaceView.value = 'corrections';
    } else {
      benchmarkWorkspaceView.value = 'base';
    }
    return;
  }
  const costWorkspaceTargets = {
    acquisition_land_class: 'policy',
    acquisition_land_subclass: 'policy',
    acquisition_land_class_confirmed: 'policy',
    local_compensation_policy_name: 'policy',
    local_compensation_policy_no: 'policy',
    local_compensation_policy_date: 'policy',
    cost_approx_analysis: 'costs',
  };
  if (costWorkspaceTargets[targetField]) {
    activeProcessMethodKey.value = 'cost_approx';
    costWorkspaceView.value = costWorkspaceTargets[targetField];
  }
  if (targetField === 'income_cap_analysis') {
    activeProcessMethodKey.value = 'income_cap';
    incomeWorkspaceView.value = 'instances';
  }
};

const processWorkspaceFallbackIds = (targetField) => {
  const text = String(targetField || '');
  if (text.startsWith('cost_approx_analysis.')) {
    const view = costWorkspaceView.value;
    return [
      view === 'policy' ? 'focus_item_cost_approx_policy' : '',
      view === 'adjustments' ? 'focus_item_cost_approx_adjustments' : '',
      view === 'costs' ? 'focus_item_cost_approx_analysis' : '',
      'focus_item_cost_approx_policy',
      'focus_item_cost_approx_analysis',
      'focus_item_cost_approx_adjustments'
    ].filter(Boolean);
  }
  if (text.startsWith('market_comp_analysis.')) {
    return [
      marketWorkspaceView.value === 'factors' ? 'focus_item_market_comp_factors' : '',
      'focus_item_market_comp_analysis',
      'focus_item_market_comp_factors'
    ].filter(Boolean);
  }
  if (text.startsWith('income_cap_analysis.')) {
    return [
      incomeWorkspaceView.value === 'parameters' ? 'focus_item_income_cap_parameters' : '',
      incomeWorkspaceView.value === 'factors' ? 'focus_item_income_cap_factors' : '',
      incomeWorkspaceView.value === 'instances' ? 'focus_item_income_cap_analysis' : '',
      'focus_item_income_cap_analysis',
      'focus_item_income_cap_factors',
      'focus_item_income_cap_parameters'
    ].filter(Boolean);
  }
  if (text.startsWith('benchmark_corr_analysis.')) {
    return [
      benchmarkWorkspaceView.value === 'factors' ? 'focus_item_benchmark_corr_analysis_regional' : '',
      benchmarkWorkspaceView.value === 'corrections' ? 'focus_item_benchmark_corr_analysis_corrections' : '',
      benchmarkWorkspaceView.value === 'base' ? 'focus_item_benchmark_corr_analysis' : '',
      'focus_item_benchmark_corr_analysis',
      'focus_item_benchmark_corr_analysis_regional',
      'focus_item_benchmark_corr_analysis_corrections'
    ].filter(Boolean);
  }
  return [];
};

const resolveProcessFocusElement = (targetField) => {
  const focusId = `focus_item_${sourceKeyFragment(targetField)}`;
  return (
    document.getElementById(focusId)
    || processWorkspaceFallbackIds(targetField).map(id => document.getElementById(id)).find(Boolean)
    || document.getElementById(`focus_item_${targetField.split('.')[0]}`)
  );
};

const focusNestedProcessField = (key) => {
  const targetField = normalizeHotspotTargetField(key);
  const metadata = FIELD_REGISTRY[targetField];
  const isProcessField = (
    String(targetField).startsWith('income_cap_analysis.')
    || String(targetField).startsWith('market_comp_analysis.')
    || String(targetField).startsWith('cost_approx_analysis.')
    || String(targetField).startsWith('benchmark_corr_analysis.')
  );
  activeTab.value = isProcessField ? 'p5' : (metadata?.tab || 'p5');
  revealWorkspaceForField(targetField);

  if (targetField.includes('.rent_factor_items.')) {
    const parts = targetField.split('.');
    const idx = parts.indexOf('rent_factor_items');
    if (idx !== -1 && parts[idx + 1]) {
      const factorKey = parts[idx + 1];
      const f = (incomeAnalysis.value?.rent_factor_items || []).find(item => item.key === factorKey);
      if (f) {
        f.tempExpanded = true;
      }
    }
  }
  if (targetField.includes('.factors.')) {
    const parts = targetField.split('.');
    const idx = parts.indexOf('factors');
    if (idx !== -1 && parts[idx + 1]) {
      const factorKey = parts[idx + 1];
      const f = (marketAnalysis.value?.factors || []).find(item => item.key === factorKey);
      if (f) openFactorGuide(f);
    }
  }
  if (targetField === 'market_comp_analysis.monthly_growth_rate' || targetField === 'market_comp_analysis.land_reduction_rate') {
    const factorKey = targetField.endsWith('monthly_growth_rate') ? 'transaction_time' : 'use_term';
    const f = (marketAnalysis.value?.factors || []).find(item => item.key === factorKey);
    if (f) openFactorGuide(f);
  }
  nextTick(() => setTimeout(() => {
    const el = resolveProcessFocusElement(targetField);
    if (el) {
      revealFieldElement(el);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = el.querySelector('input, select, textarea');
      input?.focus?.({ preventScroll: true });
    } else {
      showToast(`未能定位“${metadata?.label || targetField}”的来源控件，请重新计算后再试`, 'warning');
    }
    triggerFieldHighlight(targetField);
  }, 140));
};

const scrollToField = (key) => {
  isMissingFieldsDialogOpen.value = false;
  // 智能别名转换，部分字段比如证书等可以定位其基础容器
  let targetField = key;
  if (key === 'plot_ratio_min') targetField = 'plot_ratio_min';
  else if (key === 'plot_ratio') targetField = 'plot_ratio';
  else if (key === 'set_plot_ratio_min') targetField = 'set_plot_ratio_min';
  else if (key === 'set_plot_ratio') targetField = 'set_plot_ratio';
  else if (key === 'right_cert_no') targetField = 'right_cert_no';
  else if (key === 'real_estate_cert_no') targetField = 'real_estate_cert_no';

  if (
    targetField === 'valuation_basis_docs_list'
    && activeTab.value === 'p5'
    && activeProcessMethodKey.value === 'cost_approx'
  ) {
    costWorkspaceView.value = 'policy';
    nextTick(() => {
      const el = document.getElementById('focus_item_cost_tax_basis_docs')
        || document.getElementById('focus_item_cost_approx_policy');
      if (el) {
        revealFieldElement(el);
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        triggerFieldHighlight('valuation_basis_docs_list', 3000);
        return;
      }
      showToast('未能定位成本法税费依据编辑区，请在“政策与征收地类”中补充', 'warning');
    });
    return;
  }

  const metadata = FIELD_REGISTRY[targetField];
  if (metadata && metadata.tab) {
    activeTab.value = metadata.tab;
  }
  revealWorkspaceForField(targetField);

  nextTick(() => {
    const id = `focus_item_${targetField}`;
    const el = document.getElementById(id);
    if (el) {
      revealFieldElement(el);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      triggerFieldHighlight(targetField, 3000);
    } else {
      showToast(`未能在页面上定位到该输入框，请在“${metadata?.section || '表单'}”中查找`, 'warning');
    }
  });
};

const basePriceFieldAliases = {
  base_land_price_doc_no: 'base_price_doc_no',
  base_land_price_doc_name: 'base_price_doc_name',
  base_land_price_publish_date: 'base_price_publish_date',
  base_land_price_pub_date: 'base_price_publish_date',
  base_land_price_date: 'base_price_base_date',
  base_land_price_value_date: 'base_price_base_date',
  base_land_price_doc_authority: 'base_price_doc_authority',
  base_land_price_authority: 'base_price_doc_authority',
  is_base_price_expired: 'base_price_is_expired',
};

const generalHotspotFieldAliases = {
  plot_ratio_display: 'plot_ratio',
  set_plot_ratio_display: 'set_plot_ratio',
  land_usage_short: 'land_usage',
  land_usage_full: 'land_usage',
  land_usage_current_class: 'land_usage',
  land_usage_price_class: 'land_usage',
  asset_use_category: 'land_usage',
  asset_use_category_other: 'land_usage_other',
  land_use_term_years: 'land_use_term',
  buy_location_desc: 'room_detail_location',
  valuation_basis_docs_rendered: 'valuation_basis_docs_list',
};

const normalizeHotspotTargetField = (field) => {
  const baseNormalized = basePriceFieldAliases[field] || field;
  return generalHotspotFieldAliases[baseNormalized] || baseNormalized;
};
const isBasePriceHotspotField = (field) => field.startsWith('base_price_') || field.startsWith('base_land_price_') || field === 'is_base_price_expired';

const focusBasePriceDrawerField = (targetField) => {
  showBasePriceDrawer.value = true;

  nextTick(() => setTimeout(() => {
    const focusId = `focus_item_base_price_drawer_${targetField}`;
    const el = document.getElementById(focusId) || document.getElementById(`focus_item_${targetField}`);
    const drawerBody = document.querySelector('.base-price-drawer-body');

    if (el) {
      revealFieldElement(el);
      if (drawerBody && drawerBody.contains(el)) {
        const top = el.offsetTop - drawerBody.clientHeight / 2 + el.clientHeight / 2;
        drawerBody.scrollTo({ top: Math.max(top, 0), behavior: 'smooth' });
      } else {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      const input = el.querySelector('input, select, textarea');
      input?.focus?.({ preventScroll: true });
    }

    triggerFieldHighlight(targetField);
  }, 360));
};

const handlePerspectiveRefClick = (seg) => {
  const rawTargetField = seg.field || (seg.fields && seg.fields[0]);
  if (!rawTargetField) return;

  const targetField = normalizeHotspotTargetField(rawTargetField);
  if (isBasePriceHotspotField(rawTargetField) || isBasePriceHotspotField(targetField)) {
    focusBasePriceDrawerField(targetField);
    return;
  }

  const reg = FIELD_REGISTRY[targetField];
  if (!reg) return;
  activeTab.value = reg.tab;
  revealWorkspaceForField(targetField);

  nextTick(() => setTimeout(() => {
    const el = document.getElementById(`focus_item_${targetField}`);
    if (el) {
      revealFieldElement(el);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = el.querySelector('input, select, textarea');
      input?.focus?.({ preventScroll: true });
    }

    triggerFieldHighlight(targetField);
  }, 120));
};

const handleProcessSegmentClick = (seg) => {
  const rawTargetField = seg.field || (seg.fields && seg.fields[0]);
  if (!rawTargetField) return;
  focusProcessSource(rawTargetField);
};

// 5. 换肤控制 (支持冷色温浅色切换
const toggleTheme = () => {
  isLightTheme.value = !isLightTheme.value;
  localStorage.setItem('theme', isLightTheme.value ? 'light' : 'dark');
  if (isLightTheme.value) {
    document.documentElement.classList.add('light-theme');
  } else {
    document.documentElement.classList.remove('light-theme');
  }
};

// ==============================================================================
// 📥 测算表拖拽解析
// ==============================================================================
const handleDragOver = () => {
  isDragging.value = true;
};

const handleDragLeave = () => {
  isDragging.value = false;
};

const handleFileDrop = async (e) => {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files.length === 0) return;
  
  const file = files[0];
  if (!file.name.endsWith('.xlsx')) {
    showToast('❌ 仅支持拖入.xlsx 格式的测算表', 'error');
    return;
  }
  
  const formData = new FormData();
  formData.append('file', file);
  
  isLoading.value = true;
  loadingMessage.value = '正在一键安全解析Excel 测算表..';
  
  try {
    const response = await fetch('/api/parse-excel', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || '接口解析失败');
    }
    
    const res = await response.json();
    
    excelMetadata.name = res.excel_name;
    excelMetadata.md5 = res.md5_checksum;
    
    const back_data = res.data;
    Object.keys(back_data).forEach(key => {
      const incomingValue = back_data[key];
      if (form[key] && incomingValue !== '' && incomingValue !== null && incomingValue !== undefined && incomingValue !== '______') {
        const currentValue = String(form[key].value || '').trim();
        if (form[key].is_dirty && currentValue) {
          return;
        }
        form[key].value = incomingValue;
        form[key].origin = generatedBackfillKeys.has(key) ? 'generated' : 'excel_imported';
        form[key].is_dirty = false;
      }
    });
    land_registration_desc_segments.value = back_data.land_registration_desc_segments || [];
    land_right_desc_segments.value = back_data.land_right_desc_segments || [];
    land_use_status_desc_segments.value = back_data.land_use_status_desc_segments || [];
    updateValuationSegments(back_data);
    syncLegacyLandUsageFields();
    syncPlotRatioDisplay(true);
    regenerateOwnershipDraft(false);
    regenerateValuationNarratives(false);
    
    activeTab.value = 'p1';
    
    showToast('🎉 Excel 测算表成功一键解析并回填！');
  } catch (error) {
    showToast(`❌ 解析失败: ${error.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

// ==============================================================================
// 📷 证照 OCR 直贴提取
// ==============================================================================
const handleOcrExtract = async () => {
  if (!ocrRawText.value.trim()) {
    showToast('⚠ 请先粘贴待识别的原始文本', 'warning');
    return;
  }
  
  isLoading.value = true;
  loadingMessage.value = '正在调用离线高精度匹配引擎提取指标...';
  
  try {
    const response = await fetch('/api/ocr', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        raw_text: ocrRawText.value,
        attachment_type: ocrType.value
      })
    });
    
    if (!response.ok) {
      throw new Error('OCR 提取服务连接失败');
    }
    
    const res = await response.json();
    const matchCount = applyExtractedFields(res.data, 'ocr_extracted', '离线剪贴板输入txt');
    
    if (matchCount > 0) {
      showToast(`🎉 离线提取成功！已生成 ${matchCount} 条待确认证据。`);
    } else {
      showToast('⚠ 提取成功但未能匹配到对应字段，请检查文本是否正确', 'warning');
    }
    
  } catch (error) {
    showToast(`❌ OCR 识别提取阶段失败: ${error.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

const handleOcrFileUpload = async (event) => {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;

  isLoading.value = true;
  loadingMessage.value = '正在读取附件文字层并提取指标...';

  let totalMatches = 0;
  const extractedTexts = [];
  const failures = [];

  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('attachment_type', ocrType.value);
      formData.append('min_text_chars', String(ocrMinTextChars.value ?? 80));

      const response = await fetch('/api/ocr-file', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        let message = '附件识别失败';
        try {
          const err = await response.json();
          message = err.detail || message;
        } catch (_) {}
        failures.push(`${file.name}: ${message}`);
        continue;
      }

      const res = await response.json();
      totalMatches += applyExtractedFields(res.data, 'ocr_extracted', file.name);
      
      const cleanedAttName = cleanFileName(file.name);
      if (!uploadedAttachments.value.some(att => att.cleanedName === cleanedAttName)) {
        uploadedAttachments.value.push({
          name: file.name,
          cleanedName: cleanedAttName
        });
      }
      
      if (res.text) {
        extractedTexts.push(`【${file.name}｜${res.extraction_method}】\n${res.text}`);
      }
    }

    if (extractedTexts.length) {
      ocrRawText.value = extractedTexts.join('\n\n---\n\n');
    }

    if (totalMatches > 0) {
      activeTab.value = 'p3';
      showOCR.value = true;
      showToast(`🎉 附件识别完成，已生成 ${totalMatches} 条待确认证据。`);
    } else if (extractedTexts.length) {
      showToast('⚠ 附件已提取文字，但未匹配到表单字段，请检查附件类型选择。', 'warning');
    }

    if (failures.length) {
      showToast(`⚠ 部分附件未能识别：${failures[0]}`, 'warning');
    }
  } catch (error) {
    showToast(`❌ 附件识别失败: ${error.message}`, 'error');
  } finally {
    isLoading.value = false;
    event.target.value = '';
  }
};

// ==============================================================================
// 📄 高保真 A4 渲染与即用即销预览
// ==============================================================================
const buildReportRenderData = ({ archiveToResult = true, outputType = '' } = {}) => {
  syncLegacyLandUsageFields();
  syncPlotRatioDisplay(true);
  const renderData = {};
  Object.keys(form).forEach(key => {
    renderData[key] = form[key].value;
  });
  renderData['plot_ratio_display'] = buildPlotRatioDisplay();
  
  renderData['excel_name'] = excelMetadata.name || '桌面端手工微调填报';
  renderData['md5_checksum'] = excelMetadata.md5 || 'MANUAL_VER_NO_CHECKSUM';
  renderData['archive_to_result'] = archiveToResult;
  renderData['site_photo_data_urls'] = sitePhotoItems.value.map(item => item.dataUrl);
  renderData['site_photo_captions'] = sitePhotoItems.value.map(item => item.caption || item.name);

  if (outputType) {
    renderData['render_output_type'] = outputType;
  }

  return renderData;
};

const buildFormExportPayload = () => {
  syncLegacyLandUsageFields();
  syncPlotRatioDisplay(true);
  const data = {};
  Object.keys(form).forEach(key => {
    data[key] = {
      value: form[key].value,
      origin: form[key].origin,
      is_dirty: form[key].is_dirty
    };
  });
  return {
    data,
    meta: {
      excel_name: excelMetadata.name || '桌面端手工微调填报',
      md5_checksum: excelMetadata.md5 || 'MANUAL_VER_NO_CHECKSUM',
      project_name: form.project_name.value,
      land_location: form.land_location.value,
      site_photo_count: sitePhotoItems.value.length
    }
  };
};

const exportCurrentForm = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  loadingMessage.value = '正在导出当前填报表单...';
  try {
    const response = await fetch('/api/export-form', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildFormExportPayload())
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || '表单导出失败');
    }
    const blob = await response.blob();
    const baseName = form.land_location.value || form.project_name.value || '估价填报表单';
    downloadBlobFile(blob, `${baseName}_表单导出_${fileTimestamp()}.xlsx`);
    showToast('当前表单已导出为 Excel。');
  } catch (error) {
    showToast(`表单导出失败：${error.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

const buildWordReportFileName = () => {
  const prjName = form.land_location.value || '自动生成的估价报告';
  return `${prjName.replace(/[\\/:*?"<>|]/g, '_')}_高保真Word 报告_${new Date().getTime()}.docx`;
};

const fetchRenderedReportBlob = async (renderData) => {
  const response = await fetch('/api/render-report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(renderData)
  });

  if (!response.ok) {
    let message = '渲染引擎响应失败';
    try {
      const err = await response.json();
      message = err.detail || message;
    } catch {
      const text = await response.text();
      message = text || message;
    }
    throw new Error(message);
  }

  return response.blob();
};

const triggerWordDownload = (blob) => {
  if (wordDownloadUrl.value) {
    URL.revokeObjectURL(wordDownloadUrl.value);
  }
  wordDownloadFileName.value = buildWordReportFileName();
  wordDownloadUrl.value = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = wordDownloadUrl.value;
  link.download = wordDownloadFileName.value;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const downloadWordReport = async (options = {}) => {
  const silent = Boolean(options?.silent);
  const manageLoading = !isLoading.value;
  if (manageLoading) {
    isLoading.value = true;
    loadingMessage.value = '正在生成并下载Word 报告...';
  }

  try {
    const renderData = buildReportRenderData({ archiveToResult: false, outputType: 'docx' });
    const blob = await fetchRenderedReportBlob(renderData);
    triggerWordDownload(blob);
    if (!silent) {
      showToast('🎉 Word 报告已生成并下载！');
    }
    return true;
  } catch (error) {
    showToast(`⚠ Word 报告下载失败: ${error.message}`, silent ? 'warning' : 'error');
    return false;
  } finally {
    if (manageLoading) {
      isLoading.value = false;
    }
  }
};

const handleRenderReport = async () => {
  isLoading.value = true;
  loadingMessage.value = '正在物理渲染并转换为高保真A4 PDF 预览...';

  try {
    const renderData = buildReportRenderData({ archiveToResult: true });
    const blob = await fetchRenderedReportBlob(renderData);
    if (pdfUrl.value) {
      URL.revokeObjectURL(pdfUrl.value);
    }

    if (blob.type === 'application/pdf') {
      pdfUrlType.value = 'pdf';
      pdfUrl.value = URL.createObjectURL(blob);
      loadingMessage.value = 'PDF 预览已完成，正在自动下载 Word 报告...';
      const wordDownloaded = await downloadWordReport({ silent: true });
      if (wordDownloaded) {
        showToast('🎉 A4 PDF 预览已刷新，Word 报告已自动下载！');
      } else {
        showToast('⚠ PDF 预览已刷新，但 Word 自动下载失败，可点击“下载 Word”重试。', 'warning');
      }
    } else {
      pdfUrlType.value = 'docx';
      pdfUrl.value = URL.createObjectURL(blob);
      triggerWordDownload(blob);
      showToast('🎉 本地另存为 PDF 接口挂起，平台已自愈降级，高保真 Word 报告已为您自动下载！', 'warning');
    }
  } catch (error) {
    const errMsg = error.message || '';
    if (errMsg.includes('正式归档失败：检测到以下核心要素缺失')) {
      const prefix = '正式归档失败：检测到以下核心要素缺失或含有未填写占位符，请补齐后再提交归档：';
      let cleanMsg = errMsg.replace('❌ 高保真A4 渲染阶段失败: ', '').trim();
      cleanMsg = cleanMsg.replace(prefix, '').trim();
      
      const rawFields = cleanMsg.split('、');
      const parsedFields = [];
      rawFields.forEach(item => {
        const parts = item.split('|');
        if (parts.length === 2) {
          parsedFields.push({ label: parts[0], key: parts[1] });
        } else {
          parsedFields.push({ label: item, key: item });
        }
      });
      missingFields.value = parsedFields;
      isMissingFieldsDialogOpen.value = true;
      showToast('正式归档失败：请补足缺失的核心要素', 'error');
    } else {
      showToast(`高保真A4 渲染阶段失败: ${error.message}`, 'error');
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style>
/* 引用 style.css 里的样式 */

/* 基准地价系数修正娉曞伐作区 */
.benchmark-result-strip strong { color: var(--color-morandi-green-strong, #6f9e7f); }
.benchmark-row-active { background: rgba(111, 158, 127, 0.18); font-weight: 600; }
.benchmark-formula-group .benchmark-formula-line {
  font-family: 'Cascadia Code', 'Consolas', monospace;
  line-height: 1.9;
  word-break: break-all;
  padding: 10px 12px;
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid var(--border-color, rgba(148, 163, 184, 0.3));
  border-radius: 6px;
}
.benchmark-formula-group .benchmark-formula-line strong {
  display: inline-block;
  margin-left: 6px;
  color: var(--color-morandi-green-strong, #6f9e7f);
  font-size: 1.05rem;
}
.method-warning-strip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 10px 0 12px;
  padding: 10px 12px;
  border-left: 3px solid var(--warning, #d08a00);
  background: rgba(245, 158, 11, 0.14);
  color: var(--text-primary, #1f2933);
  line-height: 1.6;
}
.method-warning-strip strong {
  white-space: nowrap;
  color: var(--warning, #a45f00);
}
.method-warning-strip span {
  flex: 1;
}
.method-warning-strip .warning-hotspot {
  flex-shrink: 0;
}
.benchmark-map-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}
.benchmark-map-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 220px));
  gap: 10px;
}
.benchmark-map-preview-grid .image-thumb-wrapper {
  min-height: 130px;
}

/* 证据与政策预警高级霓虹呼吸呼吸闪烁样式*/
@keyframes warning-neon-pulse {
  0% {
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1), 0 0 4px rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.25);
  }
  50% {
    box-shadow: 0 4px 16px rgba(245, 158, 11, 0.18), 0 0 10px rgba(245, 158, 11, 0.4);
    border-color: rgba(245, 158, 11, 0.6);
    background: rgba(245, 158, 11, 0.09);
  }
  100% {
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1), 0 0 4px rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.25);
  }
}

@keyframes danger-neon-pulse {
  0% {
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12), 0 0 4px rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.25);
  }
  50% {
    box-shadow: 0 4px 16px rgba(239, 68, 68, 0.22), 0 0 10px rgba(239, 68, 68, 0.55);
    border-color: rgba(239, 68, 68, 0.65);
    background: rgba(239, 68, 68, 0.09);
  }
  100% {
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12), 0 0 4px rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.25);
  }
}

.warning-card-premium.warning {
  background: rgba(245, 158, 11, 0.05);
  border-color: rgba(245, 158, 11, 0.35);
  color: #ffb74d;
  animation: warning-neon-pulse 3s infinite ease-in-out;
}

.warning-card-premium.danger {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.35);
  color: #f44336;
  animation: danger-neon-pulse 3s infinite ease-in-out;
}

.warning-ack-btn {
  color: #ffffff;
  transition: all 0.2s ease-in-out;
}
.warning-ack-btn:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: rgba(255, 255, 255, 0.35) !important;
  transform: translateY(-1px);
}
.warning-ack-btn:active {
  transform: translateY(1px);
}

/* 预警列表过渡动画（向上缩平淡出） */
.warning-list-enter-active,
.warning-list-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 80px;
}
.warning-list-enter-from {
  opacity: 0;
  transform: translateY(-12px);
  max-height: 0;
}
.warning-list-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-16px);
  max-height: 0;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  border-width: 0 !important;
}
.warning-list-move {
  transition: transform 0.4s ease;
}

.premium-details summary:hover {
  color: var(--accent-hover) !important;
}
.premium-details[open] {
  border-style: solid !important;
  background: rgba(255, 255, 255, 0.03) !important;
}

/* 📋 缺失字段检查清单 Modal 极度 premium 精致现代玻璃态样式 */
.missing-fields-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: modal-backdrop-fade 0.3s ease-out;
}

.missing-fields-modal {
  width: 480px;
  max-width: 90%;
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border: 1px solid rgba(239, 68, 68, 0.35);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 0 30px rgba(239, 68, 68, 0.15);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modal-slide-up 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.missing-fields-modal .modal-header {
  padding: 16px 20px;
  background: rgba(239, 68, 68, 0.1);
  border-bottom: 1px solid rgba(239, 68, 68, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.missing-fields-modal .modal-title {
  font-size: 15px;
  font-weight: 700;
  color: #f87171;
}

.missing-fields-modal .close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  transition: color 0.2s;
}

.missing-fields-modal .close-btn:hover {
  color: #ffffff;
}

.missing-fields-modal .modal-body {
  padding: 20px;
  max-height: 380px;
  overflow-y: auto;
}

.missing-fields-modal .modal-intro {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.6;
}

.missing-fields-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.missing-field-item {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 6px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.missing-field-item:hover {
  background: rgba(239, 68, 68, 0.06);
  border-color: rgba(239, 68, 68, 0.35);
  transform: translateY(-1.5px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.08);
}

.missing-field-item .field-icon {
  margin-right: 8px;
  font-size: 14px;
}

.missing-field-item .field-label {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}

.missing-field-item .field-key {
  font-size: 11px;
  color: var(--text-secondary);
  margin-right: 12px;
}

.missing-field-item .go-modify-link {
  font-size: 12px;
  color: #38bdf8;
  font-weight: 600;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.missing-field-item:hover .go-modify-link {
  opacity: 1;
  text-shadow: 0 0 8px rgba(56, 189, 248, 0.5);
}

.missing-fields-modal .modal-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.3);
}

@keyframes modal-backdrop-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modal-slide-up {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.comparable-workspace {
  padding-bottom: 32px;
}

.comparable-view-tabs,
.comparable-actions,
.scheme-toolbar,
.analysis-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.comparable-view-tabs {
  padding: 10px 0 14px;
  border-bottom: 1px solid var(--border-color);
}

.comparable-status {
  font-size: 12px;
  color: var(--warning);
}

.comparable-status.complete {
  color: var(--success);
}

.comparable-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comparable-panel {
  padding: 16px 0;
  border-bottom: 1px solid var(--border-color);
}

.comparable-filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.access-channel-line {
  margin: 8px 0 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.access-channel-hint {
  margin: 0 0 12px;
  color: var(--warning);
  font-size: 12px;
  line-height: 1.5;
}

.cloud-proxy-settings {
  display: grid;
  grid-template-columns: minmax(145px, auto) minmax(240px, 1.4fr) minmax(180px, 1fr) auto auto auto auto;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
}

.cloud-proxy-settings .field-input {
  min-height: 32px;
}

.cloud-proxy-token-state {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.comparable-filter-grid label,
.analysis-toolbar label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 11px;
  color: var(--text-secondary);
}

.benchmark-linked-control {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.benchmark-linked-control .field-input {
  flex: 1;
  min-width: 0;
}

.benchmark-linked-control .table-action {
  flex: 0 0 auto;
  white-space: nowrap;
}

.crawl-progress,
.manual-editor,
.analysis-warnings {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
}

.crawl-progress div,
.manual-editor > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.crawl-progress progress {
  width: 100%;
  margin-top: 8px;
}

@media (max-width: 1180px) {
  .cloud-proxy-settings {
    grid-template-columns: 1fr 1fr;
  }
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
  margin-top: 12px;
}

.comparable-table {
  width: 100%;
  min-width: 1480px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 11px;
}

.comparable-table th,
.comparable-table td {
  padding: 7px 8px;
  border: 1px solid var(--border-color);
  vertical-align: middle;
  overflow-wrap: anywhere;
}

.comparable-table th {
  background: var(--bg-sidebar);
  color: var(--text-primary);
}

.comparable-table td small,
.selected-case-grid small {
  display: block;
  margin-top: 3px;
  color: var(--text-secondary);
}

.slot-actions {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.slot-actions button,
.table-action {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-primary);
  padding: 4px 7px;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-checkbox {
  width: 22px;
  height: 22px;
  min-width: 22px;
  accent-color: var(--accent);
  cursor: pointer;
}

.cost-bulk-toolbar {
  display: flex;
  justify-content: flex-end;
  margin: 0 0 8px;
}

.slot-actions button.selected {
  border-color: var(--accent);
  background: var(--highlight-bg);
  color: var(--accent);
}

.code-editor {
  margin: 10px 0;
  height: auto;
  font-family: Consolas, "Microsoft YaHei", monospace;
  line-height: 1.5;
}

.comparable-drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1800;
  background: var(--drawer-overlay);
  backdrop-filter: blur(2px);
}

.comparable-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: min(720px, 96vw);
  height: 100%;
  overflow-y: auto;
  padding: 18px;
  border-left: 1px solid var(--border-color);
  background: var(--drawer-bg);
  color: var(--text-primary);
  box-shadow: -18px 0 42px rgba(0, 0, 0, 0.38);
}

.factor-guide-drawer {
  width: min(920px, 96vw);
}

.comparable-drawer-header,
.comparable-drawer-actions,
.scheme-factor-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comparable-drawer-header {
  position: sticky;
  top: -18px;
  z-index: 2;
  justify-content: space-between;
  padding: 14px 0;
  background: var(--drawer-bg);
  border-bottom: 1px solid var(--border-color);
}

.comparable-drawer-header small {
  display: block;
  margin-top: 4px;
  color: var(--drawer-text-secondary);
}

.case-status-strip,
.analysis-summary-strip {
  display: grid;
  gap: 8px;
}

.case-status-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 14px 0;
}

.case-status-strip span {
  padding: 8px;
  border-left: 3px solid var(--success);
  background: rgba(255, 255, 255, 0.035);
  font-size: 12px;
}

.case-status-strip span.pending {
  border-left-color: var(--warning);
  color: var(--warning);
}

.case-drawer-section {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
}

.case-drawer-section h3,
.scheme-group h3 {
  margin: 0 0 10px;
  font-size: 14px;
}

.case-summary-grid,
.case-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.case-summary-grid > div {
  min-height: 56px;
  padding: 8px;
  background: var(--drawer-surface);
  border-left: 2px solid var(--border-color);
}

.case-summary-grid span,
.case-summary-grid strong {
  display: block;
}

.case-summary-grid span,
.case-field-grid small,
.analysis-summary-strip small {
  color: var(--text-secondary);
  font-size: 11px;
}

.case-summary-grid strong {
  margin-top: 4px;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.case-field-grid label,
.factor-guide-drawer label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
}

.case-field-grid em {
  margin-left: 4px;
  font-style: normal;
  font-size: 10px;
}

.source-draft,
.source-missing {
  color: var(--warning);
}

.source-confirmed {
  color: var(--success);
}

.source-official {
  color: var(--accent);
}

.advanced-section {
  margin-top: 14px;
  color: var(--text-secondary);
}

.advanced-section summary {
  cursor: pointer;
  font-size: 12px;
}

.comparable-drawer-actions {
  position: sticky;
  bottom: -18px;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 12px 0;
  border-top: 1px solid var(--border-color);
  background: var(--drawer-bg);
}

.comparable-drawer-actions span {
  margin-right: auto;
  color: var(--drawer-text-secondary);
  font-size: 11px;
}

.scheme-toolbar .field-input {
  max-width: 260px;
}

.scheme-editor {
  margin-top: 14px;
}

.scheme-impact-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border-left: 3px solid var(--warning);
  background: var(--drawer-surface);
}

.scheme-impact-banner span {
  color: var(--text-secondary);
  font-size: 12px;
}

.scheme-name-field {
  display: grid;
  grid-template-columns: 90px minmax(240px, 1fr);
  align-items: center;
  max-width: 620px;
  gap: 8px;
  font-size: 12px;
}

.scheme-group {
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.scheme-group h3 span {
  color: var(--text-secondary);
  font-weight: normal;
  font-size: 11px;
}

.scheme-factor-card {
  margin-top: 8px;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.02);
}

.scheme-factor-heading {
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.scheme-factor-heading > .field-input:first-child {
  flex: 1 1 220px;
}

.scheme-factor-heading select {
  width: auto;
  min-width: 100px;
}

.factor-level-table {
  margin-top: 8px;
}

.factor-level-table > div {
  display: grid;
  grid-template-columns: 110px 86px minmax(220px, 1fr) auto;
  gap: 6px;
  margin-bottom: 6px;
}

.analysis-toolbar {
  margin-bottom: 12px;
}

.analysis-toolbar strong {
  margin-right: auto;
}

.compact-input {
  width: 86px;
}

.cost-na-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 86px;
  min-height: 32px;
  padding: 0 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.045);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.cost-coefficient-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 86px;
}

.cost-coefficient-cell .compact-input {
  width: 86px;
}

.cost-zone-suggestion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin: 8px 0 12px;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
}

.cost-zone-suggestion strong {
  color: var(--text-primary);
}

.cost-inline-warning {
  margin: 0 0 10px;
  padding: 8px 10px;
  border-left: 3px solid #d4a017;
  background: rgba(212, 160, 23, 0.08);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.cost-derived-summary-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.cost-derived-summary-line span {
  padding: 5px 8px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--surface-muted);
}

.cost-status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.cost-status-pill.ok {
  background: rgba(33, 150, 123, 0.15);
  color: var(--success);
}

.cost-status-pill.warning {
  background: rgba(212, 160, 23, 0.16);
  color: #b7791f;
}

.cost-status-pill.manual {
  background: rgba(67, 97, 238, 0.14);
  color: var(--accent);
}

.cost-status-pill.pending {
  background: rgba(219, 39, 119, 0.12);
  color: #be185d;
}

.cost-status-pill.muted {
  background: var(--surface-muted);
  color: var(--text-secondary);
}

.compact-action {
  min-height: 28px;
  padding: 4px 8px;
  font-size: 12px;
}

.cost-price-field-links {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.danger-action {
  border-color: rgba(220, 38, 38, 0.35);
  color: #b91c1c;
}

.is-disabled-row {
  opacity: 0.55;
}

.cost-readonly-usage {
  display: block;
  min-width: 118px;
  padding: 7px 9px;
  border: 1px solid var(--border-color);
  background: var(--surface-muted);
  color: var(--text-primary);
  font-weight: 600;
}

.cost-land-class-confirm {
  align-self: flex-end;
  flex-direction: row !important;
  align-items: center;
  min-height: 34px;
  padding: 0 8px;
}

.analysis-summary-strip {
  grid-template-columns: repeat(6, minmax(105px, 1fr));
  margin-bottom: 12px;
}

.analysis-summary-strip > div {
  min-height: 64px;
  padding: 8px;
  border-left: 3px solid var(--accent);
  background: rgba(255, 255, 255, 0.025);
}

.analysis-summary-strip span,
.analysis-summary-strip strong,
.analysis-summary-strip small {
  display: block;
}

.analysis-summary-strip strong {
  margin: 5px 0 2px;
  font-size: 16px;
}

.factor-cell {
  width: 100%;
  min-height: 76px;
  padding: 7px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.025);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.factor-cell span,
.factor-cell strong,
.factor-cell small {
  display: block;
}

.factor-cell strong {
  margin: 5px 0;
}

.factor-cell small {
  color: var(--text-secondary);
}

.factor-cell.confirmed {
  border-left: 3px solid var(--success);
}

.factor-cell.warning {
  border-left: 3px solid var(--warning);
}

.factor-guide-help {
  padding: 10px;
  border-left: 3px solid var(--accent);
  color: var(--drawer-text-secondary);
  background: var(--drawer-surface);
  line-height: 1.6;
}

.factor-level-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.factor-level-options button {
  min-height: 92px;
  padding: 9px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  background: var(--drawer-surface);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.factor-level-options button.selected {
  border-color: var(--accent);
  background: var(--drawer-surface-strong);
  box-shadow: inset 3px 0 0 var(--accent);
}

.factor-level-options strong,
.factor-level-options span,
.factor-level-options small {
  display: block;
}

.factor-level-options span {
  margin: 5px 0;
  color: var(--accent);
}

.factor-level-options small {
  color: var(--drawer-text-secondary);
  line-height: 1.4;
}

.selected-case-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.selected-case-grid > div {
  min-height: 74px;
  padding: 10px;
  border-left: 3px solid var(--accent);
  background: rgba(255, 255, 255, 0.025);
}

.selected-case-grid span {
  display: block;
  margin-top: 5px;
  overflow-wrap: anywhere;
}

.analysis-warnings {
  color: var(--warning);
}

.warning-reference-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 30px;
  padding: 5px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.35);
}

.warning-reference-line:last-child {
  border-bottom: 0;
}

.warning-hotspot {
  flex: 0 0 auto;
  padding: 4px 7px;
  border: 1px solid var(--warning);
  border-radius: 4px;
  background: var(--bg-card);
  color: var(--warning);
  font-size: 11px;
  cursor: pointer;
}

.market-evidence-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  margin: 12px 0;
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--warning);
  background: var(--bg-card);
}

.market-evidence-panel.complete {
  border-left-color: var(--success);
}

.market-evidence-panel strong,
.market-evidence-panel span,
.market-evidence-panel small {
  display: block;
}

.market-evidence-panel span,
.market-evidence-panel small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.market-evidence-files {
  margin: -4px 0 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
}

.market-evidence-files > div {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: 8px;
  padding: 7px 9px;
  border-bottom: 1px solid var(--border-color);
  font-size: 11px;
}

.market-evidence-files > div:last-child {
  border-bottom: 0;
}

.market-evidence-files span {
  color: var(--text-secondary);
  overflow-wrap: anywhere;
}

.market-evidence-upload-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 12px 0;
}

.market-evidence-card {
  padding: 10px;
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--accent);
  background: var(--bg-card);
}

.market-evidence-card header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.market-evidence-card strong,
.market-evidence-card small,
.market-evidence-card p {
  display: block;
}

.market-evidence-card small,
.market-evidence-card p,
.market-evidence-kind-row small {
  color: var(--text-secondary);
  font-size: 11px;
}

.market-evidence-card p {
  min-height: 34px;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}

.market-evidence-kind-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(130px, 1.2fr);
  gap: 8px;
  align-items: center;
  padding: 7px 0;
  border-top: 1px solid var(--border-color);
}

.market-evidence-kind-row input[type="file"] {
  width: 100%;
  color: var(--text-secondary);
  font-size: 11px;
}

.factor-table td .field-input {
  min-width: 120px;
  margin-bottom: 4px;
}

.confirm-line {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-secondary);
}

.cost-flow-nav {
  position: sticky;
  top: 0;
  z-index: 3;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 0.75rem 0 1rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  opacity: 0.72;
  transition: opacity 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.cost-flow-nav:hover {
  opacity: 1;
  background: var(--bg-card);
  border-color: var(--border-color, #dbe3ef);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
}

.cost-flow-nav:hover .cost-flow-nav-label,
.cost-flow-nav:hover .table-action {
  opacity: 1;
}

.cost-flow-nav .cost-flow-nav-label,
.cost-flow-nav .table-action {
  opacity: 0.88;
  transition: opacity 0.2s ease;
}

.cost-help-icon-btn {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 999px;
  border: 1.5px solid var(--border-color, #94a3b8);
  background: transparent;
  color: var(--text-secondary);
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.cost-help-icon-btn:hover {
  border-color: var(--primary-color, #2563eb);
  color: var(--primary-color, #2563eb);
  background: rgba(37, 99, 235, 0.08);
}

.cost-policy-help-modal {
  width: min(920px, 92vw);
  max-width: 92vw;
}

.cost-building-add-modal {
  width: min(1080px, 96vw);
  max-width: 96vw;
}

.cost-policy-help-modal .modal-body,
.cost-building-add-modal .modal-body {
  max-height: min(70vh, 620px);
  overflow-y: auto;
}

.cost-help-table th,
.cost-help-table td {
  white-space: normal;
  word-break: break-word;
}

.cost-help-group-cell {
  vertical-align: top;
  font-weight: 700;
  background: rgba(37, 99, 235, 0.08);
  border-right: 1px solid rgba(148, 163, 184, 0.35);
}

.cost-policy-help-modal .modal-footer .icon-btn:not(.primary),
.cost-building-add-modal .modal-footer .icon-btn:not(.primary) {
  color: #e2e8f0;
  border: 1px solid rgba(226, 232, 240, 0.45);
  background: rgba(148, 163, 184, 0.12);
}

.cost-building-add-table tbody tr {
  cursor: pointer;
}

.cost-building-add-table tbody tr.cost-row-selected {
  background: rgba(37, 99, 235, 0.16);
}

.cost-building-add-table tbody tr.cost-row-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.cost-help-formula-block {
  margin-top: 0.75rem;
  color: var(--text-secondary);
  font-size: 0.92rem;
}

.cost-pricing-assistant {
  position: fixed;
  right: 1.25rem;
  bottom: 1.25rem;
  z-index: 1200;
  width: min(420px, calc(100vw - 2rem));
  max-height: min(80vh, 640px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-card);
  box-shadow: var(--shadow);
}

.cost-pricing-assistant-header {
  position: sticky;
  top: 0;
  z-index: 2;
  flex: 0 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  cursor: move;
  user-select: none;
}

.cost-pricing-assistant-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0.75rem 1rem 1rem;
  display: grid;
  gap: 0.75rem;
}

.cost-pricing-field {
  display: grid;
  gap: 0.35rem;
}

.cost-pricing-formula {
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.cost-pricing-controls {
  display: grid;
  gap: 0.5rem;
}

.cost-pricing-control-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 0.5rem;
  align-items: center;
}

.cost-pricing-control-label {
  font-size: 0.85rem;
}

.cost-pricing-changed {
  color: var(--warning, #f59e0b);
  font-weight: 700;
}

.cost-pricing-changes {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.cost-pricing-entry-points {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.cost-flow-nav-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-right: 0.25rem;
}

.market-workspace-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 0;
  padding-bottom: 10px;
  overflow-x: auto;
  border-bottom: 1px solid var(--border-color);
}

.market-workspace-panel {
  padding: 14px 0;
}

.market-scheme-source-bar,
.market-factor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
}

.market-scheme-source-bar span,
.market-scheme-source-bar strong,
.market-scheme-source-bar small,
.market-factor-toolbar strong,
.market-factor-toolbar span {
  display: block;
}

.market-scheme-source-bar span,
.market-scheme-source-bar small,
.market-factor-toolbar span {
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 11px;
}

.market-factor-filter {
  display: flex;
  gap: 6px;
}

.table-action.active {
  border-color: var(--accent);
  background: var(--highlight-bg);
  color: var(--accent);
}

.market-factor-group {
  margin-top: 14px;
}

.market-factor-group h3 {
  margin-bottom: 7px;
  font-size: 13px;
}

.market-factor-group h3 span {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: normal;
}

.market-factor-task {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 110px 120px 86px;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 9px 10px;
  margin-bottom: 6px;
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--text-secondary);
  border-radius: 5px;
  background: var(--bg-card);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.market-factor-task.complete {
  border-left-color: var(--success);
}

.market-factor-task.pending {
  border-left-color: var(--warning);
}

.market-factor-task-main strong,
.market-factor-task-main small {
  display: block;
}

.market-factor-task-main small,
.market-factor-task-progress {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.market-factor-task-warning {
  color: var(--warning);
  font-size: 11px;
}

.market-factor-task-action {
  color: var(--accent);
  font-size: 12px;
  text-align: right;
}

.factor-guide-rule,
.factor-guide-subject {
  padding: 12px;
  margin-top: 12px;
  border: 1px solid var(--border-color);
  background: var(--drawer-surface);
}

.factor-guide-rule span {
  color: var(--warning);
  font-size: 11px;
}

.factor-guide-rule p {
  margin-top: 6px;
  color: var(--drawer-text-secondary);
  line-height: 1.6;
}

.factor-guide-subject {
  display: grid;
  grid-template-columns: 150px minmax(240px, 1fr);
  align-items: end;
  gap: 12px;
}

.factor-guide-case-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.factor-guide-case {
  padding: 10px;
  border: 1px solid var(--border-color);
  background: var(--drawer-surface);
}

.factor-guide-case > header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  min-height: 48px;
  margin-bottom: 8px;
}

.factor-guide-case header small {
  display: block;
  margin-top: 3px;
  color: var(--drawer-text-secondary);
  font-size: 10px;
}

.factor-case-state {
  flex: 0 0 auto;
  color: var(--warning);
  font-size: 11px;
}

.factor-case-state.complete {
  color: var(--success);
}

.factor-guide-case .factor-level-options {
  grid-template-columns: 1fr;
  max-height: 250px;
  overflow-y: auto;
}

.factor-guide-case .factor-level-options button {
  min-height: 72px;
}

.factor-guide-fields {
  display: grid;
  grid-template-columns: 1fr 80px;
  gap: 7px;
  margin-top: 9px;
}

.factor-guide-reason {
  grid-column: 1 / -1;
}

.scheme-change-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1900;
  display: grid;
  place-items: center;
  padding: 18px;
  background: var(--drawer-overlay);
}

.scheme-change-dialog {
  width: min(620px, 96vw);
  max-height: min(720px, 90vh);
  overflow-y: auto;
  padding: 16px;
  border: 1px solid var(--border-color);
  background: var(--drawer-bg);
  color: var(--text-primary);
  box-shadow: var(--shadow);
}

.scheme-change-dialog header,
.scheme-change-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.scheme-change-dialog header small {
  display: block;
  margin-top: 4px;
  color: var(--drawer-text-secondary);
}

.scheme-change-list {
  margin: 14px 0;
  padding-left: 22px;
  color: var(--drawer-text-secondary);
  line-height: 1.7;
}

.scheme-change-actions {
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.process-toolbar,
.process-method-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.process-empty {
  padding: 24px 0;
  color: var(--text-secondary);
}

.process-method-tabs {
  padding: 10px 0 14px;
  border-bottom: 1px solid var(--border-color);
}

.process-state-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-left: 6px;
  border-radius: 50%;
  background: var(--warning);
}

.process-state-dot.complete {
  background: var(--success);
}

.process-state-dot.skeleton {
  background: var(--text-secondary);
}

.process-status-band,
.process-results {
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 1px;
  margin: 14px 0;
  border: 1px solid var(--border-color);
  background: var(--border-color);
}

.process-status-band > div,
.process-results > div {
  min-height: 64px;
  padding: 10px;
  background: var(--bg-card);
}

.process-status-band span,
.process-status-band strong,
.process-results span,
.process-results strong,
.process-results small {
  display: block;
}

.process-status-band span,
.process-results span,
.process-results small {
  color: var(--text-secondary);
  font-size: 11px;
}

.process-status-band strong,
.process-results strong {
  margin-top: 6px;
}

.process-warnings {
  padding: 8px 10px;
  border-left: 3px solid var(--warning);
  background: rgba(255, 255, 255, 0.025);
}

.process-content-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  position: relative;
}

.process-local-nav {
  grid-column: 1;
  grid-row: 1;
  justify-self: start;
  position: sticky;
  top: 12px;
  width: 180px;
  max-height: calc(100vh - 120px);
  overflow: auto;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-card);
  transform: translateX(calc(-100% - 16px));
  z-index: 3;
}

.process-local-nav-item {
  display: block;
  width: 100%;
  margin: 0 0 6px;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--text-secondary);
  text-align: left;
  font-size: 12px;
  line-height: 1.35;
  cursor: pointer;
}

.process-local-nav-item:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: rgba(20, 184, 166, 0.08);
}

.process-content-main {
  grid-column: 1;
  grid-row: 1;
  min-width: 0;
}

.process-section {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  scroll-margin-top: 88px;
}

.process-section header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.process-section header strong,
.process-section header small {
  display: block;
}

.process-section header small {
  margin-top: 3px;
  color: var(--text-secondary);
}

.process-section.needs-adjustment {
  padding: 12px;
  border: 1px solid rgba(245, 158, 11, 0.65);
  background: rgba(245, 158, 11, 0.1);
}

.process-review-message {
  margin: 0 0 8px;
  color: var(--warning);
  font-weight: 600;
}

.process-narrative-editor {
  min-height: 150px;
  resize: vertical;
  line-height: 1.75;
}

.process-narrative-preview {
  min-height: 70px;
  padding: 10px;
  border-left: 3px solid var(--accent);
  background: rgba(255, 255, 255, 0.025);
  white-space: pre-wrap;
  line-height: 1.75;
}

.doc-ref-span,
.process-ref-cell {
  cursor: pointer;
  color: var(--accent);
  border-bottom: 1px dashed rgba(20, 184, 166, 0.45);
}

.computed-ref-span,
.computed-ref-cell {
  color: var(--success) !important;
  border-bottom-color: rgba(34, 197, 94, 0.7) !important;
  background: rgba(34, 197, 94, 0.10);
}

.process-hotspots {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.process-table-section .comparable-table {
  min-width: 760px;
}

.process-table-section .process-report-table {
  table-layout: auto;
  min-width: 1120px;
}

.process-report-table thead th {
  vertical-align: middle;
  text-align: center;
}

.process-report-table th,
.process-report-table td {
  min-width: 72px;
  word-break: normal;
}

.process-report-table td[colspan] {
  text-align: left;
}

@media (max-width: 1280px) {
  .process-content-layout {
    display: block;
  }

  .process-local-nav {
    position: static;
    display: flex;
    gap: 6px;
    width: auto;
    max-height: none;
    overflow-x: auto;
    transform: none;
  }

  .process-local-nav-item {
    width: auto;
    min-width: 128px;
    margin: 0;
    white-space: nowrap;
  }
}

@media (max-width: 900px) {
  .process-content-layout {
    grid-template-columns: 1fr;
  }

  .process-local-nav {
    position: static;
    display: flex;
    gap: 6px;
    width: auto;
    max-height: none;
    overflow-x: auto;
    transform: none;
  }

  .process-local-nav-item {
    width: auto;
    min-width: 128px;
    margin: 0;
    white-space: nowrap;
  }

  .selected-case-grid,
  .process-status-band,
  .process-results,
  .market-evidence-upload-grid,
  .factor-guide-case-grid {
    grid-template-columns: 1fr;
  }

  .market-workspace-tabs,
  .comparable-header-actions,
  .market-scheme-source-bar,
  .market-factor-toolbar,
  .scheme-impact-banner,
  .market-evidence-panel,
  .warning-reference-line {
    align-items: stretch;
    flex-direction: column;
  }

  .market-factor-task {
    grid-template-columns: 1fr;
  }

  .market-factor-task-action {
    text-align: left;
  }

  .factor-guide-drawer,
  .comparable-drawer {
    width: 100vw;
    max-width: 100vw;
  }

  .factor-guide-subject,
  .factor-guide-fields {
    grid-template-columns: 1fr;
  }

  .factor-guide-reason {
    grid-column: auto;
  }
}
</style>
