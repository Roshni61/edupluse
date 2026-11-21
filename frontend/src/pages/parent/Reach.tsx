import React, { useState } from "react";
import { Phone, PhoneOff, Smartphone, MessageSquareText, User, School, Volume2 } from "lucide-react";
import { LADDER } from "../../types";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { parentApi, voiceApi } from "../../api/client";

type Step = "idle" | "ring" | "menu" | "update" | "callback" | "record";
const say: Record<Step, [string, string]> = {
  idle: ["", ""],
  ring: ["Incoming call from your child's school…", "உங்கள் குழந்தையின் பள்ளியிலிருந்து அழைப்பு…"],
  menu: [
    "Vanakkam. This is the weekly update. Press 1 to hear how Karthik is doing. Press 2 to ask the teacher to call you back. Press 3 to leave a voice message.",
    "வணக்கம். இது வாராந்திரத் தகவல். கார்த்திக் எப்படி இருக்கிறார் என்று கேட்க 1ஐ அழுத்துங்கள். ஆசிரியர் உங்களை அழைக்க 2ஐ அழுத்துங்கள். குரல் செய்தி அனுப்ப 3ஐ அழுத்துங்கள்.",
  ],
  update: [
    "Karthik is doing well in Science. In Maths he needs a little help with fractions. Ten minutes of practice at home would help. Thank you.",
    "அறிவியலில் கார்த்திக் நன்றாகச் செய்கிறார். கணிதத்தில் பின்னங்களில் சிறிது உதவி தேவை. வீட்டில் 10 நிமிடம் பயிற்சி செய்தால் உதவும். நன்றி.",
  ],
  callback: [
    "Done. The teacher will call you back within two school days. Thank you.",
    "சரி. இரண்டு பள்ளி நாட்களுக்குள் ஆசிரியர் உங்களை அழைப்பார். நன்றி.",
  ],
  record: [
    "Please speak after the beep. Press any key when you are done.",
    "பீப் ஒலிக்குப் பிறகு பேசுங்கள். முடிந்ததும் எந்த எண்ணையும் அழுத்துங்கள்.",
  ],
};

export default function Reach() {
  const t = useT();
  const { state, dispatch } = useStore();
  const [step, setStep] = useState<Step>("idle");

  const press = async (k: string) => {
    // Post to real /voice/simulate endpoint to record the outcome on the server
    voiceApi.simulate(k).catch(() => {});

    if (step === "menu") {
      setStep(k === "1" ? "update" : k === "2" ? "callback" : k === "3" ? "record" : "menu");
    } else if (step === "record") {
      setStep("menu");
    }
  };

  const handleToggleLowTech = async () => {
    const nextVal = !state.lowTech;
    dispatch({ t: "lowTech", v: nextVal });
    try {
      await parentApi.updatePreferences({ no_smartphone: nextVal });
    } catch {
      // Local state already updated
    }
  };

  const speak = () => {
    try {
      const u = new SpeechSynthesisUtterance(say[step][0]);
      u.lang = "en-IN";
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    } catch {
      /* optional */
    }
  };

  return (
    <div className="space-y-5">
      <header>
        <p className="label">{t("reach")}</p>
        <h1 className="mt-1 text-2xl font-bold leading-snug">No smartphone? You still get every update.</h1>
      </header>

      <label className="card flex items-center justify-between gap-3 p-4">
        <span className="flex items-center gap-3 text-sm font-bold">
          <Smartphone className="text-coral-deep" size={20} />
          {t("noPhone")}
        </span>
        <button
          role="switch"
          aria-checked={state.lowTech}
          onClick={handleToggleLowTech}
          className={`relative h-7 w-12 rounded-full transition ${state.lowTech ? "bg-leaf" : "bg-sage-2"}`}
        >
          <span
            className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all ${
              state.lowTech ? "left-6" : "left-1"
            }`}
          />
        </button>
      </label>

      <section>
        <h2 className="mb-2 text-lg font-bold">How we reach you</h2>
        <div className="space-y-2">
          {LADDER.filter((l, i) => (state.lowTech ? i >= 1 : true)).map((l) => (
            <div key={l.step} className="card flex items-start gap-3 p-3.5">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-ink-800 font-display text-sm font-bold text-white">
                {l.step}
              </span>
              <div>
                <p className="font-bold leading-tight">{l.name}</p>
                <p className="text-xs text-ink-500">{l.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="card p-4">
        <div className="flex items-start gap-3">
          <MessageSquareText className="mt-1 shrink-0 text-leaf" size={20} />
          <div>
            <p className="font-bold">Weekly SMS (works on any phone)</p>
            <p className="mt-2 rounded-2xl rounded-tl-sm bg-sage p-3 text-sm leading-relaxed">
              Karthik did well in Science this week. Maths needs a little help. Reply 1 if all is fine, 2 to request a call, 3 for the Saturday school desk.
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-start gap-3">
          <User className="mt-1 shrink-0 text-sky" size={20} />
          <p className="text-sm text-ink-700">
            <b>Family helper:</b> add a trusted neighbour or relative as an alternate contact, with your consent.
          </p>
        </div>
        <div className="mt-3 flex items-start gap-3">
          <School className="mt-1 shrink-0 text-coral-deep" size={20} />
          <p className="text-sm text-ink-700">
            <b>Saturday desk:</b> 10:00 AM to 12:00 PM. Walk in, no booking needed.
          </p>
        </div>
      </section>

      <section className="card overflow-hidden bg-ink-900 p-0 text-white">
        <div className="p-4">
          <p className="label !text-coral">Try it</p>
          <h2 className="text-xl font-bold !text-white">The weekly voice call</h2>
          <p className="text-sm text-white/70">Automated, in Tamil or English. Use the keypad.</p>
        </div>
        <div className="min-h-[150px] bg-ink-800 px-4 py-4 text-sm leading-relaxed" aria-live="polite">
          {step === "idle" ? (
            <p className="text-white/60">Press the green button to start the call.</p>
          ) : (
            <>
              <p>{say[step][0]}</p>
              <p className="mt-2 text-white/80">{say[step][1]}</p>
              <button
                onClick={speak}
                className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold"
              >
                <Volume2 size={14} />
                Read aloud
              </button>
            </>
          )}
        </div>
        <div className="grid grid-cols-3 gap-2 p-4">
          {["1", "2", "3", "4", "5", "6"].map((k) => (
            <button
              key={k}
              onClick={() => press(k)}
              disabled={step === "idle" || step === "ring"}
              className="rounded-2xl bg-white/10 py-3 text-lg font-bold disabled:opacity-40 hover:bg-white/20"
            >
              {k}
            </button>
          ))}
          <button
            onClick={() => setStep("ring")}
            className="col-span-1 flex items-center justify-center rounded-2xl bg-leaf py-3"
            aria-label="Start call"
          >
            <Phone size={20} />
          </button>
          <button
            onClick={() => (step === "ring" ? setStep("menu") : setStep("idle"))}
            className="col-span-1 rounded-2xl bg-white/10 py-3 text-xs font-bold"
          >
            {step === "ring" ? "Answer" : "Menu"}
          </button>
          <button
            onClick={() => setStep("idle")}
            className="flex items-center justify-center rounded-2xl bg-coral py-3 text-ink-900"
            aria-label="End call"
          >
            <PhoneOff size={20} />
          </button>
        </div>
      </section>
    </div>
  );
}
