import { useState } from "react";
import { useNavigate } from "react-router-dom";

import "./Onboarding.css";

const ROLES = [
  {
    id: "student",
    icon: "🎓",
    title: "O‘quvchiman",
    description:
      "Kurslar, vocabulary, testlar va video darslar orqali bilim oling.",
  },
  {
    id: "teacher",
    icon: "👨‍🏫",
    title: "O‘qituvchiman",
    description:
      "Dars bering, kurs yarating va o‘quvchilaringizni boshqaring.",
  },
  {
    id: "center",
    icon: "🏫",
    title: "Ta’lim markazini boshqaraman",
    description:
      "O‘quvchilar, o‘qituvchilar va kurslarni yagona joydan boshqaring.",
  },
  {
    id: "company",
    icon: "💼",
    title: "Kompaniya / Jamoa",
    description:
      "Jamoangiz uchun ta’lim, meeting va hamkorlik muhitini yarating.",
  },
];

const ROLE_OPTIONS = {
  student: [
    {
      id: "courses",
      icon: "📚",
      title: "Kurslar",
      description: "Tayyor kurslarni o‘rganish",
    },
    {
      id: "vocabulary",
      icon: "📖",
      title: "Vocabulary",
      description: "Yangi so‘zlarni o‘rganish",
    },
    {
      id: "grammar",
      icon: "✍️",
      title: "Grammar",
      description: "Grammatikani mustahkamlash",
    },
    {
      id: "tests",
      icon: "📝",
      title: "Testlar",
      description: "Bilimingizni tekshirish",
    },
    {
      id: "video",
      icon: "🎥",
      title: "Video darslar",
      description: "Video orqali o‘rganish",
    },
    {
      id: "speaking",
      icon: "🎙️",
      title: "Speaking",
      description: "Gapirish ko‘nikmasini rivojlantirish",
    },
  ],

  teacher: [
    {
      id: "create_courses",
      icon: "📚",
      title: "Kurs yaratish",
      description: "O‘z kurslaringizni yarating",
    },
    {
      id: "students",
      icon: "👨‍🎓",
      title: "O‘quvchilar",
      description: "O‘quvchilarni boshqarish",
    },
    {
      id: "tests",
      icon: "📝",
      title: "Test yaratish",
      description: "Bilimni baholash uchun testlar",
    },
    {
      id: "video",
      icon: "🎥",
      title: "Video darslar",
      description: "Video kontent joylash",
    },
    {
      id: "meetings",
      icon: "📹",
      title: "Meeting",
      description: "Online dars va uchrashuvlar",
    },
    {
      id: "analytics",
      icon: "📊",
      title: "Statistika",
      description: "O‘quvchilar natijalarini ko‘rish",
    },
  ],

  center: [
    {
      id: "students",
      icon: "👨‍🎓",
      title: "O‘quvchilar",
      description: "O‘quvchilarni boshqarish",
    },
    {
      id: "teachers",
      icon: "👨‍🏫",
      title: "O‘qituvchilar",
      description: "O‘qituvchilarni boshqarish",
    },
    {
      id: "courses",
      icon: "📚",
      title: "Kurslar",
      description: "Kurslarni boshqarish",
    },
    {
      id: "analytics",
      icon: "📊",
      title: "Hisobotlar",
      description: "Markaz faoliyatini kuzatish",
    },
    {
      id: "schedule",
      icon: "📅",
      title: "Jadval",
      description: "Dars jadvalini boshqarish",
    },
    {
      id: "payments",
      icon: "💳",
      title: "To‘lovlar",
      description: "To‘lovlarni boshqarish",
    },
  ],

  company: [
    {
      id: "team",
      icon: "👥",
      title: "Jamoa",
      description: "Jamoa a’zolarini boshqarish",
    },
    {
      id: "courses",
      icon: "📚",
      title: "Korporativ kurslar",
      description: "Jamoa uchun kurslar",
    },
    {
      id: "meetings",
      icon: "📹",
      title: "Meeting",
      description: "Online uchrashuvlar",
    },
    {
      id: "video",
      icon: "🎥",
      title: "Video",
      description: "Video kontent bilan ishlash",
    },
    {
      id: "analytics",
      icon: "📊",
      title: "Statistika",
      description: "Jamoa natijalarini ko‘rish",
    },
    {
      id: "workspace",
      icon: "💼",
      title: "Workspace",
      description: "Jamoa uchun ish muhiti",
    },
  ],
};

export default function Onboarding() {
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [role, setRole] = useState("");
  const [selectedOptions, setSelectedOptions] = useState([]);

  const options = role
    ? ROLE_OPTIONS[role] || []
    : [];

  function selectRole(roleId) {
    setRole(roleId);
    setSelectedOptions([]);
  }

  function toggleOption(optionId) {
    setSelectedOptions((current) => {
      if (current.includes(optionId)) {
        return current.filter(
          (id) => id !== optionId
        );
      }

      return [...current, optionId];
    });
  }

  function nextStep() {
    if (step === 1 && !role) {
      return;
    }

    if (step === 2 && selectedOptions.length === 0) {
      return;
    }

    setStep((current) => current + 1);
  }

  function previousStep() {
    setStep((current) =>
      Math.max(1, current - 1)
    );
  }

  function finishOnboarding() {
    const onboardingData = {
      role,
      interests: selectedOptions,
      completed: true,
    };

    localStorage.setItem(
      "talim_onboarding",
      JSON.stringify(onboardingData)
    );

    console.log(
      "ONBOARDING DATA:",
      onboardingData
    );

    navigate("/app");
  }

  const progress =
    step === 1
      ? 33
      : step === 2
      ? 66
      : 100;

  return (
    <div className="onboarding-page">

      {/* LEFT SIDE */}
      <aside className="onboarding-sidebar">

        <div className="onboarding-brand">
          <div className="brand-logo">
            T
          </div>

          <div>
            <div className="brand-name">
              Talim
            </div>

            <div className="brand-tagline">
              Ta'lim. Aloqa. Rivojlanish.
            </div>
          </div>
        </div>

        <div className="sidebar-content">

          <span className="sidebar-label">
            TALIM PLATFORMASI
          </span>

          <h2>
            Siz uchun
            <br />
            mos muhitni
            <br />
            yarataylik.
          </h2>

          <p>
            Bir necha qadamda o‘zingizga
            mos Talim tajribasini sozlang.
          </p>

          <div className="sidebar-illustration">
            <div className="illustration-circle">
              {step === 1 && "👋"}
              {step === 2 && "✨"}
              {step === 3 && "🚀"}
            </div>

            <div className="illustration-dot dot-one" />
            <div className="illustration-dot dot-two" />
            <div className="illustration-dot dot-three" />
          </div>

        </div>

        <div className="step-indicator">

          <div
            className={
              step >= 1
                ? "step-dot active"
                : "step-dot"
            }
          />

          <div
            className={
              step >= 2
                ? "step-dot active"
                : "step-dot"
            }
          />

          <div
            className={
              step >= 3
                ? "step-dot active"
                : "step-dot"
            }
          />

        </div>

      </aside>

      {/* RIGHT SIDE */}
      <main className="onboarding-main">

        <div className="onboarding-content">

          {/* PROGRESS */}
          <div className="onboarding-progress">

            <div className="progress-info">
              <span>
                Qadam {step} / 3
              </span>

              <span>
                {progress}%
              </span>
            </div>

            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>

          </div>

          {/* STEP 1 */}
          {step === 1 && (
            <section className="onboarding-step">

              <div className="step-heading">

                <span className="step-badge">
                  01
                </span>

                <h1>
                  Siz Talim'dan
                  <br />
                  qanday foydalanasiz?
                </h1>

                <p>
                  Sizning rolingizga qarab,
                  Talim siz uchun kerakli
                  muhitni tayyorlaydi.
                </p>

              </div>

              <div className="role-grid">

                {ROLES.map((item) => {
                  const selected =
                    role === item.id;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={[
                        "role-card",
                        selected
                          ? "selected"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() =>
                        selectRole(item.id)
                      }
                    >

                      <div className="card-icon">
                        {item.icon}
                      </div>

                      <div className="card-check">
                        {selected
                          ? "✓"
                          : ""}
                      </div>

                      <h3>
                        {item.title}
                      </h3>

                      <p>
                        {item.description}
                      </p>

                    </button>
                  );
                })}

              </div>

            </section>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <section className="onboarding-step">

              <div className="step-heading">

                <span className="step-badge">
                  02
                </span>

                <h1>
                  Sizga nimalar
                  <br />
                  kerak bo‘ladi?
                </h1>

                <p>
                  Bir nechta variantni tanlashingiz
                  mumkin. Keyinchalik ularni
                  o‘zgartirishingiz mumkin.
                </p>

              </div>

              <div className="options-grid">

                {options.map((item) => {
                  const selected =
                    selectedOptions.includes(
                      item.id
                    );

                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={[
                        "option-card",
                        selected
                          ? "selected"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() =>
                        toggleOption(
                          item.id
                        )
                      }
                    >

                      <div className="option-icon">
                        {item.icon}
                      </div>

                      <div className="option-content">

                        <h3>
                          {item.title}
                        </h3>

                        <p>
                          {item.description}
                        </p>

                      </div>

                      <div className="option-check">
                        {selected
                          ? "✓"
                          : ""}
                      </div>

                    </button>
                  );
                })}

              </div>

            </section>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <section className="onboarding-step final-step">

              <div className="success-icon">
                ✓
              </div>

              <span className="step-badge">
                03
              </span>

              <h1>
                Hammasi tayyor! 🎉
              </h1>

              <p className="final-description">
                Siz uchun Talim muhiti
                tayyorlandi. Endi o‘rganish
                va rivojlanishni boshlashingiz
                mumkin.
              </p>

              <div className="summary-card">

                <div className="summary-row">

                  <span>
                    Sizning rolingiz
                  </span>

                  <strong>
                    {
                      ROLES.find(
                        (item) =>
                          item.id === role
                      )?.title
                    }
                  </strong>

                </div>

                <div className="summary-row">

                  <span>
                    Tanlangan yo‘nalishlar
                  </span>

                  <strong>
                    {selectedOptions.length}
                  </strong>

                </div>

              </div>

            </section>
          )}

          {/* FOOTER */}
          <div className="onboarding-footer">

            {step > 1 ? (
              <button
                type="button"
                className="secondary-button"
                onClick={previousStep}
              >
                ← Orqaga
              </button>
            ) : (
              <div />
            )}

            {step < 3 ? (
              <button
                type="button"
                className="primary-button"
                disabled={
                  step === 1
                    ? !role
                    : selectedOptions.length === 0
                }
                onClick={nextStep}
              >
                Davom etish
                <span>→</span>
              </button>
            ) : (
              <button
                type="button"
                className="primary-button"
                onClick={finishOnboarding}
              >
                Talim'ni boshlash
                <span>→</span>
              </button>
            )}

          </div>

          <div className="privacy-note">
            <span>🔒</span>

            <span>
              Siz tanlagan ma'lumotlar xavfsiz
              va maxfiy saqlanadi.
            </span>
          </div>

        </div>

      </main>

    </div>
  );
}