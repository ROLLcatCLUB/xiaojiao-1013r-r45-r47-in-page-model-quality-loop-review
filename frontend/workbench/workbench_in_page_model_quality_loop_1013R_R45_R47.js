(function(){
  const STAGE_ID = "1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_INTEGRATION";
  const params = new URLSearchParams(window.location.search || "");
  const API_BASE = params.get("api") || (window.localStorage && window.localStorage.getItem("xiaobei_workbench_api_base")) || "http://127.0.0.1:8084";
  const state = {
    context: {
      lesson: "三年级美术 2-1《色彩的渐变》",
      before_text: "看图渐变，比较明度，尝试调色，展示作品。",
      context_source: "workbench/index.html in-page component"
    },
    candidateTypes: [],
    currentCandidate: null,
    currentQuality: null,
    comparison: null,
    provider: null,
    busy: false
  };

  function html(value){
    return String(value == null ? "" : value)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;")
      .replace(/'/g,"&#39;");
  }

  function endpoint(path){
    return API_BASE.replace(/\/$/,"") + path;
  }

  function toast(text){
    if (typeof window.showToast === "function") window.showToast(text);
  }

  function setBusy(value){
    state.busy = Boolean(value);
    const card = document.querySelector('[data-card="modelQualityLoop"]');
    if (card) card.classList.toggle("loading", state.busy);
  }

  async function fetchJson(path, options){
    const response = await fetch(endpoint(path), {
      headers: {"Content-Type":"application/json"},
      ...(options || {})
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.success === false) {
      const message = payload.error || payload.message || ("HTTP " + response.status);
      throw new Error(message);
    }
    return payload;
  }

  function defaultTypes(){
    return [
      {id:"teaching_process_cleanup", label:"教学过程整理"},
      {id:"courseware_script_candidate", label:"课件脚本候选"},
      {id:"classroom_display_candidate", label:"大屏呈现候选"},
      {id:"worksheet_candidate", label:"学习单候选"},
      {id:"assessment_rubric_candidate", label:"评价维度候选"}
    ];
  }

  function scoreLabel(key){
    return ({
      structure_completeness:"结构完整",
      subject_alignment:"学科贴合",
      source_alignment:"来源贴合",
      teacher_readability:"教师可读",
      actionability:"可执行",
      hallucination_risk:"虚构风险",
      revision_value:"修改价值"
    })[key] || key;
  }

  function renderCandidate(){
    const candidate = state.currentCandidate;
    if (!candidate) {
      return '<div class="mql-candidate mql-empty">还没有候选。先点上方任一生成按钮，结果会直接回填在这里。</div>';
    }
    const missing = (candidate.missing_requirements || []).map(item => `<div class="mql-meta-item">缺口：${html(item)}</div>`).join("");
    const risks = (candidate.risk_notes || []).map(item => `<div class="mql-meta-item">风险：${html(item)}</div>`).join("");
    return `
      <div class="mql-candidate">${html(candidate.candidate_content || "")}</div>
      <div class="mql-meta-list">
        <div class="mql-meta-item">类型：${html(candidate.candidate_label || candidate.candidate_type)} / ${html(candidate.status || "generated")}</div>
        <div class="mql-meta-item">目标位置：${html(candidate.target_slot || "当前页面候选预览槽")}</div>
        <div class="mql-meta-item">来源：${html(candidate.source || "")}；provider_called=${String(Boolean(candidate.provider_called))}；sandbox_only=true</div>
        ${missing || '<div class="mql-meta-item">缺口：暂无新增缺口，仍需老师确认。</div>'}
        ${risks}
      </div>
    `;
  }

  function renderQuality(){
    const quality = state.currentQuality;
    if (!quality) {
      return '<div class="mql-empty">生成候选后，这里显示结构、学科贴合、来源贴合、教师可读等评分。</div>';
    }
    if (quality.status === "blocked") {
      return `<div class="mql-empty">当前候选被阻断：${html(quality.blocked_reason || "依据不足")}</div>`;
    }
    const scores = quality.scores || {};
    const cells = Object.keys(scores).map(key => `
      <div class="mql-score"><span>${html(scoreLabel(key))}</span><b>${html(scores[key])}</b></div>
    `).join("");
    return `
      <div class="mql-score-grid">${cells}</div>
      <div class="mql-meta-list">
        <div class="mql-meta-item">总分：${html(quality.total_score)}/35；过线：${String(Boolean(quality.basic_quality_pass))}</div>
        <div class="mql-meta-item">需要人工重点看：${String(Boolean(quality.requires_human_attention))}</div>
        <div class="mql-meta-item">调整方向：${html((quality.adjustment_points || []).join("；") || "暂无")}</div>
      </div>
    `;
  }

  function renderComparison(){
    const comparison = state.comparison;
    if (!comparison) return '<div id="mqlComparison" class="mql-comparison"></div>';
    const text = `v1 ${comparison.v1_score}/35，v2 ${comparison.v2_score}/35，变化 ${comparison.improvement_delta}；improved=${String(Boolean(comparison.improved))}`;
    return `<div id="mqlComparison" class="mql-comparison show">${html(text)}</div>`;
  }

  function render(){
    const card = document.querySelector('[data-card="modelQualityLoop"]');
    if (!card) return;
    const types = state.candidateTypes.length ? state.candidateTypes : defaultTypes();
    const beforeText = document.getElementById("mqlBeforeText");
    const adjustment = document.getElementById("mqlAdjustmentText");
    const beforeValue = beforeText ? beforeText.value : state.context.before_text;
    const adjustmentValue = adjustment ? adjustment.value : "";
    card.innerHTML = `
      <div class="section-head">
        <div class="section-head-left">
          <div class="section-icon done">M</div>
          <div>
            <div class="section-num">R45-R47</div>
            <div class="section-title">模型候选沙盒</div>
          </div>
        </div>
        <div class="section-head-right">
          <span class="pill pill-done">页面内预览</span>
          <span class="pill off">不保存</span>
        </div>
      </div>
      <div class="section-divider"></div>
      <div class="section-body mql-shell" data-stage="${STAGE_ID}">
        <div class="mql-status">
          <span>来源：${html(state.context.context_source || "workbench in-page")}</span>
          <span>API：${html(API_BASE)}</span>
          <span>模型：${html((state.provider && state.provider.model) || "checking")}</span>
        </div>
        <div class="mql-boundary">候选只用于预览和质量观察，不会保存到正式备课本。sandbox_only=true；formal_apply_allowed=false；不会写数据库、飞书、记忆，也不会覆盖原教案。</div>
        <div class="mql-grid">
          <div class="mql-box">
            <strong>当前上下文 / 原文</strong>
            <textarea id="mqlBeforeText" class="mql-textarea">${html(beforeValue || state.context.before_text)}</textarea>
            <div class="component-actions mql-button-row">
              ${types.map(item => `<button class="btn ai" type="button" data-mql-generate="${html(item.id)}">${html(item.label)}</button>`).join("")}
            </div>
            <strong style="margin-top:12px">调整要求</strong>
            <textarea id="mqlAdjustmentText" class="mql-textarea" placeholder="例如：更像三年级课堂，少一点空话，步骤再清楚些。">${html(adjustmentValue)}</textarea>
            <div class="component-actions">
              <button class="btn primary" type="button" id="mqlRegenerateBtn">按调整要求再生成</button>
            </div>
          </div>
          <div class="mql-box">
            <strong>候选内容</strong>
            ${renderCandidate()}
          </div>
        </div>
        <div class="mql-grid">
          <div class="mql-box">
            <strong>质量评分</strong>
            ${renderQuality()}
          </div>
          <div class="mql-box">
            <strong>v1 / v2 对比</strong>
            ${renderComparison()}
          </div>
        </div>
      </div>
    `;
  }

  async function loadState(){
    try {
      const payload = await fetchJson("/api/prep-room/model-quality/state");
      state.context = payload.context || state.context;
      state.candidateTypes = payload.candidate_types || defaultTypes();
      state.provider = payload.provider || null;
      render();
    } catch (error) {
      state.provider = {model:"fallback", status_error:String(error.message || error)};
      render();
    }
  }

  async function generate(candidateType){
    const beforeText = document.getElementById("mqlBeforeText")?.value || state.context.before_text;
    const adjustmentText = document.getElementById("mqlAdjustmentText")?.value || "";
    setBusy(true);
    try {
      const payload = await fetchJson("/api/prep-room/model-quality/generate", {
        method: "POST",
        body: JSON.stringify({candidate_type:candidateType, before_text:beforeText, adjustment_text:adjustmentText})
      });
      state.currentCandidate = payload.candidate;
      state.currentQuality = payload.quality_panel;
      state.comparison = null;
      toast("候选已回填到当前页面");
    } catch (error) {
      state.currentCandidate = {
        candidate_type: candidateType,
        candidate_label: candidateType,
        status: "blocked",
        source: "frontend_error",
        candidate_content: "本地接口暂时不可用：" + String(error.message || error),
        missing_requirements: ["确认本地 API 是否启动"],
        risk_notes: ["未写入正式备课本"]
      };
      state.currentQuality = {status:"blocked", blocked_reason:String(error.message || error)};
    } finally {
      setBusy(false);
      render();
    }
  }

  async function regenerate(){
    if (!state.currentCandidate) {
      toast("请先生成一个候选");
      return;
    }
    const beforeText = document.getElementById("mqlBeforeText")?.value || state.context.before_text;
    const adjustmentText = document.getElementById("mqlAdjustmentText")?.value || "";
    setBusy(true);
    try {
      const payload = await fetchJson("/api/prep-room/model-quality/regenerate", {
        method: "POST",
        body: JSON.stringify({
          candidate_type: state.currentCandidate.candidate_type,
          before_text: beforeText,
          adjustment_text: adjustmentText,
          previous_candidate: state.currentCandidate
        })
      });
      state.currentCandidate = payload.candidate;
      state.currentQuality = payload.quality_panel;
      state.comparison = payload.comparison;
      toast("已按调整要求再生成");
    } catch (error) {
      state.comparison = {v1_score:0, v2_score:0, improvement_delta:0, improved:false};
      state.currentQuality = {status:"blocked", blocked_reason:String(error.message || error)};
    } finally {
      setBusy(false);
      render();
    }
  }

  function install(){
    const grid = document.getElementById("componentGrid");
    if (!grid || document.querySelector('[data-card="modelQualityLoop"]')) return false;
    const card = document.createElement("article");
    card.className = "component doc-section model-quality-loop";
    card.dataset.card = "modelQualityLoop";
    const candidate = document.querySelector('[data-card="candidate"]');
    if (candidate && candidate.parentElement === grid) candidate.insertAdjacentElement("afterend", card);
    else grid.insertBefore(card, grid.firstChild);
    render();
    loadState();
    return true;
  }

  document.addEventListener("click", event => {
    const generateBtn = event.target.closest("[data-mql-generate]");
    if (generateBtn) {
      generate(generateBtn.dataset.mqlGenerate);
      return;
    }
    if (event.target.closest("#mqlRegenerateBtn")) regenerate();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
  window.XIAOBEI_IN_PAGE_MODEL_QUALITY_LOOP_R45_R47 = {install, loadState, generate, regenerate, state};
})();
