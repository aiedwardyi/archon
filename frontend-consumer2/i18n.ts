export type Lang = 'en' | 'ko';

const translations = {
  en: {
    whatCanIBuild: 'What can I build for you?',
    describeProject: 'Describe your project in detail...',
    generate: 'Generate',
    preview: 'Preview',
    brief: 'Brief',
    buildPlan: 'Build Plan',
    versions: 'Versions',
    whatWasBuilt: 'What Was Built',
    logs: 'Logs',
    publish: 'Publish',
    askForChanges: 'What would you like to change?',
    restoreVersion: 'Restore to this version',
    buildingApp: 'Your app is being built...',
    creatingBrief: 'Creating your brief...',
    planningBuild: 'Planning your build...',
    writingCode: 'Writing your code...',
    code: 'Code',
    versionTimeline: 'Version Timeline',
    everythingBuilt: 'Everything your AI team built',
    tasksFinalized: 'Tasks Finalized',
    selectFile: 'Select a file to view its contents',
    buildInProgress: 'Build in progress...',
    downloadReport: 'Download Report',
    livePreview: 'Live Preview',
    noPreview: 'Preview awaits generation...',
    pressEnter: 'Press ↵ to launch pipeline',
    projects: 'Projects',
  },
  ko: {
    whatCanIBuild: '무엇을 만들어 드릴까요?',
    describeProject: '프로젝트를 자세히 설명해 주세요...',
    generate: '생성하기',
    preview: '미리보기',
    brief: '기획서',
    buildPlan: '개발 계획',
    versions: '버전 기록',
    whatWasBuilt: '개발 내역',
    logs: '로그',
    publish: '배포하기',
    askForChanges: '어떤 변경을 원하시나요?',
    restoreVersion: '이 버전으로 복원',
    buildingApp: '앱을 만들고 있습니다...',
    creatingBrief: '기획서를 작성하고 있습니다...',
    planningBuild: '개발 계획을 세우고 있습니다...',
    writingCode: '코드를 작성하고 있습니다...',
    code: '코드',
    versionTimeline: '버전 타임라인',
    everythingBuilt: 'AI 팀이 만든 모든 것',
    tasksFinalized: '완료된 작업',
    selectFile: '파일을 선택하여 내용을 확인하세요',
    buildInProgress: '빌드 진행 중...',
    downloadReport: '리포트 다운로드',
    livePreview: '실시간 미리보기',
    noPreview: '미리보기 대기 중...',
    pressEnter: '↵를 눌러 파이프라인 시작',
    projects: '프로젝트',
  },
} as const;

export function t(lang: Lang, key: keyof typeof translations['en']): string {
  return translations[lang][key] || translations['en'][key];
}

export function getLang(): Lang {
  return (localStorage.getItem('archon_lang') as Lang) || 'en';
}

export function setLang(lang: Lang) {
  localStorage.setItem('archon_lang', lang);
}
