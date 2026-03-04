export type Language = "en" | "ko";

export const translations = {
  // Navbar
  projects: { en: "Projects", ko: "프로젝트" },
  pipeline: { en: "Pipeline", ko: "파이프라인" },
  versions: { en: "Versions", ko: "버전" },
  artifacts: { en: "Artifacts", ko: "아티팩트" },

  // Navbar breadcrumb
  buildAModern: { en: "Build a modern", ko: "모던 빌드" },

  // Avatar dropdown
  signedInAs: { en: "Signed in as", ko: "로그인 계정" },
  profile: { en: "Profile", ko: "프로필" },
  settings: { en: "Settings", ko: "설정" },
  pricing: { en: "Pricing", ko: "요금제" },
  documentation: { en: "Documentation", ko: "문서" },
  theme: { en: "Theme", ko: "테마" },
  design: { en: "Design", ko: "디자인" },
  light: { en: "Light", ko: "라이트" },
  dark: { en: "Dark", ko: "다크" },
  enterprise: { en: "Enterprise", ko: "기업용" },
  studio: { en: "Studio", ko: "스튜디오" },
  credits: { en: "Credits", ko: "크레딧" },
  upgradeToPro: { en: "Upgrade to Pro", ko: "Pro로 업그레이드" },
  signOut: { en: "Sign out", ko: "로그아웃" },

  // Welcome Banner
  goodMorning: { en: "Good morning", ko: "좋은 아침이에요" },
  goodAfternoon: { en: "Good afternoon", ko: "좋은 오후예요" },
  goodEvening: { en: "Good evening", ko: "좋은 저녁이에요" },
  platformOverview: { en: "Platform overview", ko: "플랫폼 개요" },
  enterpriseWorkspace: { en: "Enterprise Workspace", ko: "엔터프라이즈 워크스페이스" },
  allSystemsOperational: { en: "All systems operational", ko: "모든 시스템 정상" },
  backendOffline: { en: "Backend offline", ko: "백엔드 오프라인" },
  pipelinesToday: { en: "Pipelines Today", ko: "오늘 파이프라인" },
  linesGenerated: { en: "Lines Generated", ko: "생성된 라인" },
  avgPromptScore: { en: "Avg Prompt Score", ko: "평균 프롬프트 점수" },
  avgBuildScore: { en: "Avg Build Score", ko: "평균 빌드 점수" },
  versionsShipped: { en: "Versions Shipped", ko: "배포된 버전" },
  avgBuildTime: { en: "Avg Build Time", ko: "평균 빌드 시간" },

  // Stats
  totalProjects: { en: "Total Projects", ko: "전체 프로젝트" },
  running: { en: "Building", ko: "빌딩 중" },
  completed: { en: "Completed", ko: "완료" },
  failed: { en: "Failed", ko: "실패" },

  // Projects page
  searchProjects: { en: "Search projects...", ko: "프로젝트 검색..." },
  allStatuses: { en: "All statuses", ko: "모든 상태" },
  newProject: { en: "New Project", ko: "새 프로젝트" },
  projectName: { en: "Project Name", ko: "프로젝트 이름" },
  projectDescription: { en: "Description", ko: "설명" },
  creating: { en: "Creating…", ko: "생성 중…" },
  create: { en: "Create", ko: "만들기" },
  cancel: { en: "Cancel", ko: "취소" },

  // Delete modal
  deleteNProjects: { en: "Delete {n} project?", ko: "{n}개 프로젝트 삭제?" },
  deleteCannotUndo: { en: "This action cannot be undone.", ko: "이 작업은 취소할 수 없습니다." },
  deleteListWarning: { en: "The following project and all associated versions will be permanently deleted:", ko: "다음 프로젝트와 모든 버전 기록이 영구 삭제됩니다:" },
  typeDeleteToConfirm: { en: "Type DELETE to confirm:", ko: "삭제 확인을 위해 DELETE를 입력하세요:" },

  // Project table
  project: { en: "Project", ko: "프로젝트" },
  id: { en: "ID", ko: "ID" },
  status: { en: "Status", ko: "상태" },
  lastRun: { en: "Last Run", ko: "마지막 실행" },
  created: { en: "Created", ko: "생성일" },
  selected: { en: "selected", ko: "선택됨" },
  export_: { en: "Export", ko: "내보내기" },
  delete_: { en: "Delete", ko: "삭제" },
  showing: { en: "Showing", ko: "표시" },
  of: { en: "of", ko: "/" },
  previous: { en: "Previous", ko: "이전" },
  next: { en: "Next", ko: "다음" },

  // Activity Feed
  recentActivity: { en: "Recent Activity", ko: "최근 활동" },
  live: { en: "Live", ko: "실시간" },

  // Pipeline chat
  you: { en: "You", ko: "나" },

  // Pipeline
  conversation: { en: "Conversation", ko: "대화" },
  messages: { en: "messages", ko: "메시지" },
  agentPipeline: { en: "Agent Pipeline", ko: "에이전트 파이프라인" },
  complete: { en: "complete", ko: "완료" },
  liveOutput: { en: "Live Output", ko: "실시간 출력" },
  entries: { en: "entries", ko: "항목" },
  buildDetails: { en: "Build Details", ko: "빌드 상세" },
  model: { en: "Model", ko: "모델" },
  tokensUsed: { en: "Tokens Used", ko: "사용된 토큰" },
  estCost: { en: "Est. Cost", ko: "예상 비용" },
  creditsUsed: { en: "Credits Used", ko: "사용된 크레딧" },
  duration: { en: "Duration", ko: "소요 시간" },
  whatWouldYouLikeToBuild: { en: "What would you like to build?", ko: "무엇을 만들고 싶으세요?" },

  // Pipeline agents
  requirementsAgent: { en: "Requirements Agent", ko: "요구사항 에이전트" },
  understandsYourRequest: { en: "Understands your request", ko: "요청을 분석합니다" },
  architectureAgent: { en: "Architecture Agent", ko: "아키텍처 에이전트" },
  plansTheBuild: { en: "Plans the build", ko: "빌드를 설계합니다" },
  buildAgent: { en: "Build Agent", ko: "빌드 에이전트" },
  writesYourCode: { en: "Writes your code", ko: "코드를 작성합니다" },
  designAgent: { en: "Design Agent", ko: "디자인 에이전트" },
  generatesVisuals: { en: "Generates visuals", ko: "비주얼을 생성합니다" },
  done: { en: "Done", ko: "완료" },
  building: { en: "Building…", ko: "빌드 중…" },
  pending: { en: "Pending", ko: "대기 중" },
  selectProjectFirst: { en: "Select a project first", ko: "먼저 프로젝트를 선택하세요" },
  selectProjectDesc: { en: "Go to the Projects tab and select a project to start building.", ko: "프로젝트 탭에서 프로젝트를 선택하여 빌드를 시작하세요." },
  pipelineAlreadyRunning: { en: "A pipeline is already running", ko: "파이프라인이 이미 실행 중입니다" },
  sending: { en: "Sending…", ko: "전송 중…" },
  send: { en: "Send", ko: "전송" },
  noMessages: { en: "No messages yet. Type a prompt below to start building.", ko: "아직 메시지가 없습니다. 아래에 프롬프트를 입력하여 빌드를 시작하세요." },

  // Versions
  versionHistory: { en: "Version History", ko: "버전 이력" },
  showVersions: { en: "Show versions", ko: "버전 보기" },
  downloadReport: { en: "Download Report", ko: "보고서 다운로드" },
  pipelineFailed: { en: "Pipeline failed.", ko: "파이프라인이 실패했습니다." },
  restoreToThisVersion: { en: "Restore to this version", ko: "이 버전으로 복원" },
  filesChanged: { en: "files changed", ko: "파일 변경" },
  whatWasBuilt: { en: "What Was Built", ko: "빌드 내용" },
  livePreview: { en: "Live Preview", ko: "실시간 미리보기" },
  prompt: { en: "Prompt", ko: "프롬프트" },
  brief: { en: "Brief", ko: "브리프" },
  buildPlan: { en: "Build Plan", ko: "빌드 계획" },
  code: { en: "Code", ko: "코드" },

  // Artifacts
  plan: { en: "Plan", ko: "계획" },
  tasks: { en: "Tasks", ko: "작업" },
  logs: { en: "Logs", ko: "로그" },
  preview: { en: "Preview", ko: "미리보기" },
  governance: { en: "Governance", ko: "거버넌스" },
  publish: { en: "Publish", ko: "배포" },
  downloadCode: { en: "Download Code", ko: "코드 다운로드" },
  rawData: { en: "Raw Data", ko: "원시 데이터" },
  requirements: { en: "Requirements", ko: "요구사항" },
  architecture: { en: "Architecture", ko: "아키텍처" },
  reproducible: { en: "Reproducible", ko: "재현 가능" },
  verified: { en: "Verified", ko: "검증됨" },
  overview: { en: "Overview", ko: "개요" },
  goals: { en: "Goals", ko: "목표" },
  successCriteria: { en: "Success Criteria", ko: "성공 기준" },
  coreFeatures: { en: "Core Features (MVP)", ko: "핵심 기능 (MVP)" },
  whatWereBuilding: { en: "What We're Building", ko: "구현 내용" },
  targetUsers: { en: "Target Users", ko: "타겟 사용자" },
  whoWereBuildingFor: { en: "Who We're Building For", ko: "사용자 대상" },
  milestones: { en: "milestones", ko: "마일스톤" },
  generatedBy: { en: "Generated by", ko: "생성:" },
  assignee: { en: "Assignee", ko: "담당자" },
  requirementsDoc: { en: "Requirements doc", ko: "요구사항 문서" },
  architecturePlan: { en: "Architecture plan", ko: "아키텍처 계획" },
  files: { en: "files", ko: "파일" },
  yesterday: { en: "Yesterday", ko: "어제" },

  // Profile Modal
  fullName: { en: "Full Name", ko: "이름" },
  email: { en: "Email", ko: "이메일" },
  memberSince: { en: "Member Since", ko: "가입일" },

  // Settings Modal
  apiKeysSecurityNotice: { en: "API keys are stored locally and never sent to our servers.", ko: "API 키는 로컬에 저장되며 서버로 전송되지 않습니다." },
  saveApiKeys: { en: "Save API Keys", ko: "API 키 저장" },

  // Pricing Modal
  chooseThePlan: { en: "Choose the plan that fits your agency.", ko: "에이전시에 맞는 플랜을 선택하세요." },
  free: { en: "Free", ko: "무료" },
  pro: { en: "Pro", ko: "Pro" },
  forever: { en: "forever", ko: "영구" },
  perMonth: { en: "/ month", ko: "/ 월" },
  currentPlan: { en: "Current Plan", ko: "현재 플랜" },

  // NotFound
  pageNotFound: { en: "404", ko: "404" },
  oops: { en: "Oops! Page not found", ko: "페이지를 찾을 수 없습니다" },
  returnHome: { en: "Return to Home", ko: "홈으로 돌아가기" },

  // Governance tab
  govFactsheet: { en: "AI Factsheet", ko: "AI 팩트시트" },
  govGenerated: { en: "Generated", ko: "생성일" },
  govHighQuality: { en: "High Quality", ko: "고품질" },
  govGoodQuality: { en: "Good Quality", ko: "양호" },
  govLowQuality: { en: "Low Quality", ko: "저품질" },
  govScore: { en: "Score", ko: "점수" },
  govDownloadClientPdf: { en: "Download Client PDF", ko: "고객용 PDF 다운로드" },
  govDownloadInternalPdf: { en: "Download Internal PDF", ko: "내부용 PDF 다운로드" },
  govUiArchetype: { en: "UI Archetype", ko: "UI 아키타입" },
  govAgentSequence: { en: "Agent Sequence", ko: "에이전트 순서" },
  govAutoDetected: { en: "Auto-detected", ko: "자동 감지" },
  govPromptQuality: { en: "Prompt Quality", ko: "프롬프트 품질" },
  govPromptQualityDesc: { en: "How clearly your idea was communicated to the AI pipeline", ko: "아이디어가 AI 파이프라인에 얼마나 명확하게 전달되었는지" },
  govWatsonNotConfigured: { en: "Watson NLU credentials not configured — add WATSON_NLU_API_KEY and WATSON_NLU_URL to backend/.env to enable prompt scoring.", ko: "Watson NLU 자격 증명이 설정되지 않았습니다. 프롬프트 점수를 활성화하려면 backend/.env에 WATSON_NLU_API_KEY 및 WATSON_NLU_URL을 추가하세요." },
  govBuildQuality: { en: "Build Quality Score", ko: "빌드 품질 점수" },
  govBuildQualityDesc: { en: "Based on code output, archetype detection, and pipeline success", ko: "코드 출력, 아키타입 감지 및 파이프라인 성공 여부 기반" },
  govFactor: { en: "Factor", ko: "요인" },
  govPoints: { en: "Points", ko: "점수" },
  govNote: { en: "Note", ko: "비고" },
  govModelRegistry: { en: "Model Registry", ko: "모델 레지스트리" },
  govAgentRole: { en: "Agent Role", ko: "에이전트 역할" },
  govProvider: { en: "Provider", ko: "제공사" },
  govAiProcessing: { en: "AI Processing", ko: "AI 처리" },
  govOutputs: { en: "Outputs", ko: "출력 결과" },
  govFilesGenerated: { en: "Files Generated", ko: "생성된 파일" },
  govImagesGenerated: { en: "Images Generated", ko: "생성된 이미지" },
  govQualityIndicators: { en: "Quality Indicators", ko: "품질 지표" },
  govCompliance: { en: "Compliance", ko: "컴플라이언스" },
  govComplianceDesc: { en: "This build was generated by a governed, auditable AI pipeline.", ko: "이 빌드는 거버넌스를 갖춘 감사 가능한 AI 파이프라인에 의해 생성되었습니다." },
  govFactsheetNotAvailable: { en: "Factsheet not available for this version. Run a new build to generate one.", ko: "이 버전의 팩트시트가 없습니다. 새 빌드를 실행하여 생성하세요." },
  govNoFactsheet: { en: "No factsheet data.", ko: "팩트시트 데이터가 없습니다." },
  govLoadingFactsheet: { en: "Loading factsheet...", ko: "팩트시트 로딩 중..." },
  govPoweredByWatson: { en: "Powered by IBM Watson NLU", ko: "IBM Watson NLU 제공" },
  govExcellent: { en: "Excellent", ko: "우수" },
  govFair: { en: "Fair", ko: "보통" },
  govDomain: { en: "Domain", ko: "도메인" },
  govKeywords: { en: "Keywords", ko: "키워드" },
  govAuditTrail: { en: "Audit Trail", ko: "감사 추적" },
  govVersionHistory: { en: "Version History", ko: "버전 이력" },
  govArtifactRetention: { en: "Artifact Retention", ko: "아티팩트 보존" },
  govHumanReviewRequired: { en: "Human Review Required", ko: "사람 검토 필요" },
  govPdfFailed: { en: "PDF download failed", ko: "PDF 다운로드 실패" },
  govAiModelsProcessed: { en: "{count} AI model(s) processed this build across {providers}.", ko: "이 빌드는 {providers}의 {count}개 AI 모델로 처리되었습니다." },
} as const;

export type TranslationKey = keyof typeof translations;

export const t = (key: TranslationKey, lang: Language): string => {
  return translations[key][lang];
};
