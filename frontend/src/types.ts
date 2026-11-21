/**
 * Shared Frontend Types and UI Configurations.
 * Replaces legacy mock.ts dependencies with server-first type safety.
 */

export type Level = 1 | 2 | 3;
export type BadgeCat = "Effort" | "Growth" | "Consistency" | "Community" | "Curiosity";

export const LEVEL_NAME: Record<Level, string> = {
  1: "Keep an eye",
  2: "Needs support",
  3: "Needs support now",
};

export interface Badge {
  id: string;
  name: string;
  cat: BadgeCat;
  how: string;
  icon: string;
  earned?: boolean;
  earned_at?: string;
}

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

export const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export const WINDOWS = [
  { id: "am", label: "Before school", time: "7:30 to 8:15 AM", slots: ["7:30", "7:35", "7:40", "7:45", "7:50", "7:55"], extended: false },
  { id: "lunch", label: "Lunch break", time: "1:00 to 1:40 PM", slots: ["1:00", "1:05", "1:10", "1:15", "1:20", "1:25"], extended: false },
  { id: "pm", label: "After school", time: "4:15 to 5:00 PM", slots: ["4:15", "4:20", "4:25", "4:30", "4:35", "4:40"], extended: false },
  { id: "eve", label: "Evening (Tue and Thu)", time: "6:30 to 7:30 PM", slots: ["6:30", "6:35", "6:40", "6:45", "6:50", "6:55"], extended: true },
];

export const LADDER = [
  { step: 1, name: "App or WhatsApp", count: 14, desc: "Weekly summary plus a 3-tap check-in" },
  { step: 2, name: "SMS with reply codes", count: 5, desc: "Reply 1 if going well, 2 to request a call" },
  { step: 3, name: "Automated voice call", count: 3, desc: "Tamil or English. Press 1 to hear, 2 for a callback" },
  { step: 4, name: "Teacher callback", count: 2, desc: "A real person, in a short slot" },
  { step: 5, name: "School desk, Saturday", count: 1, desc: "Face to face, no phone needed" },
];

export interface Mission {
  id: string;
  title: string;
  minutes: number;
  xp: number;
  tier: "Starter" | "Steady" | "Stretch";
  kind: "quiz" | "help" | "ask";
  badge?: string;
  blurb: string;
}

export const MISSIONS: Mission[] = [
  { id: "m1", title: "Fraction warm-up", minutes: 5, xp: 30, tier: "Starter", kind: "quiz", badge: "personal-best", blurb: "Three friendly questions. No marks lost for wrong answers." },
  { id: "m2", title: "Explain it to a friend", minutes: 3, xp: 20, tier: "Starter", kind: "help", badge: "helping-hand", blurb: "Pick one idea from today and explain it to a classmate." },
  { id: "m3", title: "Ask one doubt", minutes: 2, xp: 15, tier: "Starter", kind: "ask", badge: "question-asker", blurb: "Anything you're unsure about. Your teacher sees it without your name on it." },
];
