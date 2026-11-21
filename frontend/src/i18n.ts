import { useStore } from "./store";

const dict = {
  en: {
    hello: "Hello, Karthik's family", glance: "This week at a glance", well: "What went well", tryHome: "One thing to try at home",
    checkin: "Weekly check-in", checkinQ: "How was this week at home?", great: "Great", okay: "Okay", hard: "Hard",
    voice: "Voice note", send: "Send", book: "Book a 5-minute call", teacherCalls: "Teacher calls my phone", voiceNotes: "Voice notes, reply when I'm free",
    visit: "Visit school on Saturday", video: "Video link", reminders: "Reminders", confirm: "Confirm", noPhone: "I don't use a smartphone",
    thanks: "Thank you", wellText: "Karthik is doing great in Science and has been finishing his practice missions.",
    tryText: "Ten minutes of fractions practice at home could help.",
    summary: "In Maths his scores dipped over three tests and he missed four Mondays.",
    nextCall: "Your next call", reach: "Reach me",
    signIn: "Sign in to EduPulse",
    signInDesc: "Access your role-specific dashboard with secure role and school scoping.",
    emailLabel: "Email address",
    passwordLabel: "Password",
    signInBtn: "Sign In",
    signingIn: "Signing in...",
    logoutBtn: "Log out",
    quickDemoHeading: "Demo Quick-Login",
    quickDemoSub: "Click any profile to sign in instantly with seeded demo data:",
    demoTeacher: "Teacher (Ms. Priya)",
    demoStudent: "Student (Karthik R)",
    demoParent: "Parent (Karthik's Mother)",
    demoAdmin: "Admin (HM Ramanathan)",
  },
  ta: {
    hello: "வணக்கம், கார்த்திக்கின் குடும்பத்தினரே", glance: "இந்த வார சுருக்கம்", well: "நன்றாக நடந்தவை", tryHome: "வீட்டில் முயற்சிக்க ஒரு விஷயம்",
    checkin: "வாராந்திர கருத்து", checkinQ: "இந்த வாரம் வீட்டில் எப்படி இருந்தது?", great: "சிறப்பு", okay: "பரவாயில்லை", hard: "கடினம்",
    voice: "குரல் செய்தி", send: "அனுப்பு", book: "5 நிமிட அழைப்பை முன்பதிவு செய்யுங்கள்", teacherCalls: "ஆசிரியர் எனக்கு அழைப்பார்", voiceNotes: "குரல் செய்தி, நேரம் கிடைக்கும்போது பதில் சொல்கிறேன்",
    visit: "சனிக்கிழமை பள்ளிக்கு வருகிறேன்", video: "வீடியோ இணைப்பு", reminders: "நினைவூட்டல்கள்", confirm: "உறுதிசெய்", noPhone: "என்னிடம் ஸ்மார்ட்போன் இல்லை",
    thanks: "நன்றி", wellText: "அறிவியலில் கார்த்திக் சிறப்பாகச் செய்து வருகிறார்; பயிற்சிப் பணிகளையும் முடித்து வருகிறார்.",
    tryText: "வீட்டில் தினமும் 10 நிமிடம் பின்னங்கள் பயிற்சி செய்தால் உதவும்.",
    summary: "கணிதத்தில் கடந்த மூன்று தேர்வுகளில் மதிப்பெண் சற்றுக் குறைந்துள்ளது; நான்கு திங்கட்கிழமைகள் வரவில்லை.",
    nextCall: "உங்கள் அடுத்த அழைப்பு", reach: "என்னைத் தொடர்பு கொள்ள",
    signIn: "எடுபல்ஸ் உள்நுழைவு",
    signInDesc: "பாதுகாப்பான அனுமதியுடன் உங்கள் பொறுப்பிற்குரிய திரையை அணுகுங்கள்.",
    emailLabel: "மின்னஞ்சல் முகவரி",
    passwordLabel: "கடவுச்சொல்",
    signInBtn: "உள்நுழைக",
    signingIn: "உள்நுழைகிறது...",
    logoutBtn: "வெளியேறு",
    quickDemoHeading: "மாதிரி கணக்குகள் (நேரடி உள்நுழைவு)",
    quickDemoSub: "கீழே உள்ள ஏதேனும் ஒரு பொறுப்பைத் தேர்வு செய்து நேரடியாக உள்நுழையலாம்:",
    demoTeacher: "ஆசிரியர் (பிரியா)",
    demoStudent: "மாணவர் (கார்த்திக்)",
    demoParent: "பெற்றோர் (கார்த்திக்கின் தாய்)",
    demoAdmin: "தலைமை ஆசிரியர் (ராமநாதன்)",
  },
};
export type Key = keyof typeof dict.en;
export function useT() {
  const { state } = useStore();
  return (k: Key) => dict[state.lang][k] ?? dict.en[k];
}
