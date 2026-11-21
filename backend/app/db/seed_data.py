export type Level = 1 | 2 | 3;
export type BadgeCat = "Effort" | "Growth" | "Consistency" | "Community" | "Curiosity";

export interface Student {
  id: string; name: string; subject: string; level: Level; reasons: string[]; minutes: number; benefit: number;
  actions: string[]; parentWho: string; channel: string; scores: number[]; att: number; hw: number; bright?: boolean; brightWhy?: string;
}

export const TESTS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"];
export const CLASS_AVG = [58, 59, 58, 57, 58, 58, 59, 58];

export const students: Student[] = [
  { id: "karthik", name: "Karthik", subject: "Maths", level: 3, minutes: 8, benefit: 95, att: 76, hw: 60,
    reasons: ["Maths is down 9 marks from his usual level of 73", "4 Monday absences in the last 5 weeks", "Homework late 3 times this month"],
    actions: ["10-minute fractions practice mission", "5-minute parent call", "Pair with a peer helper for ratios"],
    parentWho: "Mother", channel: "WhatsApp", scores: [74, 73, 75, 72, 68, 64, 61, 60] },
  { id: "divya", name: "Divya", subject: "Maths", level: 2, minutes: 10, benefit: 88, att: 71, hw: 38,
    reasons: ["Attendance fell to 71% over four weeks", "Homework missing 5 of the last 8", "Good sign: finished 4 Garden missions in 2 weeks"],
    actions: ["Short chat about what is getting in the way", "Voice-note check-in with parent", "Start with Starter-level missions"],
    parentWho: "Father (night shift)", channel: "Voice note", scores: [44, 41, 43, 40, 42, 41, 43, 45] },
  { id: "arun", name: "Arun", subject: "Science", level: 2, minutes: 6, benefit: 70, att: 88, hw: 70,
    reasons: ["Science down 9 marks from his usual level of 66", "Last two submissions were late"],
    actions: ["Review the last lab report together", "Try one Stretch mission"],
    parentWho: "Grandmother", channel: "Voice call (Tamil)", scores: [66, 68, 65, 67, 63, 60, 58, 57] },
  { id: "vikram", name: "Vikram", subject: "Maths", level: 2, minutes: 5, benefit: 60, att: 90, hw: 80,
    reasons: ["Ratios and proportions are the weak topic", "Quiz scores flat for three weeks"],
    actions: ["Topic mini-lesson on ratios", "Peer helper: Meena"],
    parentWho: "Mother", channel: "SMS", scores: [62, 60, 61, 59, 55, 54, 50, 52] },
  { id: "rahul", name: "Rahul", subject: "English", level: 1, minutes: 3, benefit: 30, att: 85, hw: 85,
    reasons: ["Small attendance dip on Fridays"], actions: ["Friendly check-in"],
    parentWho: "Father", channel: "WhatsApp", scores: [68, 66, 67, 66, 65, 64, 66, 63] },
  { id: "lakshmi", name: "Lakshmi", subject: "Maths", level: 1, minutes: 2, benefit: 20, att: 92, hw: 90,
    reasons: ["Marks drifting slightly lower, still within her normal range"], actions: ["Keep an eye for two more weeks"],
    parentWho: "Mother", channel: "WhatsApp", scores: [59, 60, 58, 61, 60, 59, 58, 57] },
  { id: "meena", name: "Meena", subject: "Maths", level: 1, minutes: 0, benefit: 0, att: 96, hw: 95, bright: true, brightWhy: "Up 19 marks over eight tests",
    reasons: [], actions: [], parentWho: "Mother", channel: "WhatsApp", scores: [55, 57, 60, 62, 66, 69, 72, 74] },
  { id: "sana", name: "Sana", subject: "Science", level: 1, minutes: 0, benefit: 0, att: 98, hw: 100, bright: true, brightWhy: "Longest steady climb in the class",
    reasons: [], actions: [], parentWho: "Father", channel: "WhatsApp", scores: [70, 72, 71, 74, 75, 77, 78, 80] },
];

export interface Badge { id: string; name: string; cat: BadgeCat; how: string; icon: string; }
export const BADGES: Badge[] = [
  { id: "first-step", name: "First Step", cat: "Effort", how: "Finish your very first mission.", icon: "Footprints" },
  { id: "showed-up", name: "Showed Up", cat: "Effort", how: "Complete 3 missions in one week.", icon: "Sun" },
  { id: "try-again", name: "Tried Again", cat: "Effort", how: "Retry a question after a hint.", icon: "RotateCcw" },
  { id: "personal-best", name: "Personal Best", cat: "Growth", how: "Beat your own previous best score.", icon: "TrendingUp" },
  { id: "comeback", name: "Comeback", cat: "Growth", how: "Return to missions after a break.", icon: "Rocket" },
  { id: "topic-turnaround", name: "Topic Turnaround", cat: "Growth", how: "Lift a weak topic by 15 points.", icon: "Target" },
  { id: "steady-week", name: "Steady Week", cat: "Consistency", how: "Do something every school day for a week. Rest days never break it.", icon: "CalendarCheck" },
  { id: "early-bird", name: "Early Bird", cat: "Consistency", how: "Submit homework before the deadline 3 times.", icon: "Sunrise" },
  { id: "helping-hand", name: "Helping Hand", cat: "Community", how: "Explain an idea to a classmate.", icon: "HeartHandshake" },
  { id: "class-gardener", name: "Class Gardener", cat: "Community", how: "Water the Class Garden 5 times.", icon: "Sprout" },
  { id: "question-asker", name: "Question Asker", cat: "Curiosity", how: "Ask a doubt. Good questions count.", icon: "MessageCircleQuestion" },
  { id: "explorer", name: "Explorer", cat: "Curiosity", how: "Try a Stretch mission.", icon: "Compass" },
];

export interface Mission { id: string; title: string; minutes: number; xp: number; tier: "Starter" | "Steady" | "Stretch"; kind: "quiz" | "help" | "ask"; badge?: string; blurb: string; }
export const MISSIONS: Mission[] = [
  { id: "m1", title: "Fraction warm-up", minutes: 5, xp: 30, tier: "Starter", kind: "quiz", badge: "personal-best", blurb: "Three friendly questions. No marks lost for wrong answers." },
  { id: "m2", title: "Explain it to a friend", minutes: 3, xp: 20, tier: "Starter", kind: "help", badge: "helping-hand", blurb: "Pick one idea from today and explain it to a classmate." },
  { id: "m3", title: "Ask one doubt", minutes: 2, xp: 15, tier: "Starter", kind: "ask", badge: "question-asker", blurb: "Anything you're unsure about. Your teacher sees it without your name on it." },
];

export const WINDOWS = [
  { id: "am", label: "Before school", time: "7:30 to 8:15 AM", slots: ["7:30", "7:35", "7:40", "7:45", "7:50", "7:55"], extended: false },
  { id: "lunch", label: "Lunch break", time: "1:00 to 1:40 PM", slots: ["1:00", "1:05", "1:10", "1:15", "1:20", "1:25"], extended: false },
  { id: "pm", label: "After school", time: "4:15 to 5:00 PM", slots: ["4:15", "4:20", "4:25", "4:30", "4:35", "4:40"], extended: false },
  { id: "eve", label: "Evening (Tue and Thu)", time: "6:30 to 7:30 PM", slots: ["6:30", "6:35", "6:40", "6:45", "6:50", "6:55"], extended: true },
];
export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export const BOOKED: Record<string, string> = { "Mon-am": "Meena's mother", "Tue-lunch": "Arun's grandmother", "Wed-pm": "Vikram's mother", "Thu-eve": "Rahul's father" };

export const UNREACHED = [
  { id: "u1", who: "Divya's father", why: "Night-shift worker. Two missed calls.", suggest: "Voice note, reply when free" },
  { id: "u2", who: "Arun's grandmother", why: "Feature phone. Tamil voice call not answered twice.", suggest: "Saturday school desk or a neighbour contact" },
  { id: "u3", who: "Vikram's mother", why: "No reply to the weekly summary for 2 weeks.", suggest: "SMS with reply codes, then a callback" },
];

export const LADDER = [
  { step: 1, name: "App or WhatsApp", count: 14, desc: "Weekly summary plus a 3-tap check-in" },
  { step: 2, name: "SMS with reply codes", count: 5, desc: "Reply 1 if going well, 2 to request a call" },
  { step: 3, name: "Automated voice call", count: 3, desc: "Tamil or English. Press 1 to hear, 2 for a callback" },
  { step: 4, name: "Teacher callback", count: 2, desc: "A real person, in a short slot" },
  { step: 5, name: "School desk, Saturday", count: 1, desc: "Face to face, no phone needed" },
];

export const HEAT: number[][] = [
  [1, 1, 2, 2, 1, 1], [2, 2, 3, 3, 2, 2], [1, 2, 2, 2, 1, 1], [3, 2, 2, 1, 1, 1], [1, 1, 1, 2, 2, 1], [2, 2, 2, 3, 2, 2],
];
export const HEAT_CLASSES = ["8A", "8B", "9A", "9B", "10A", "10B"];
export const EQUITY = [{ band: "Needs support", earned: 74 }, { band: "On track", earned: 81 }, { band: "Strong", earned: 85 }];
export const REACH = [{ name: "App or WhatsApp", value: 58 }, { name: "SMS", value: 18 }, { name: "Voice call", value: 12 }, { name: "Callback or in person", value: 12 }];

export function supportLevel(att: number, hw: number, drop: number): Level {
  const score = (100 - att) * 0.5 + (100 - hw) * 0.3 + drop * 1.2;
  return score >= 34 ? 3 : score >= 20 ? 2 : 1;
}
export const LEVEL_NAME: Record<Level, string> = { 1: "Keep an eye", 2: "Needs support", 3: "Needs support now" };
export function baseOf(s: Student) { return Math.round(s.scores.slice(0, 4).reduce((a, b) => a + b, 0) / 4); }
export function dropOf(s: Student) { return Math.max(0, baseOf(s) - s.scores[s.scores.length - 1]); }
export function levelFromXp(xp: number) {
  const tiers = [{ name: "Sprout", min: 0 }, { name: "Sapling", min: 200 }, { name: "Bloom", min: 450 }, { name: "Grove", min: 800 }];
  let i = 0; tiers.forEach((t, k) => { if (xp >= t.min) i = k; });
  const next = tiers[i + 1]; const cur = tiers[i];
  return { name: cur.name, next: next?.name ?? "Top", pct: next ? (xp - cur.min) / (next.min - cur.min) : 1, toNext: next ? next.min - xp : 0, index: i };
}
