import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  chart,
  text,
  image,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  fr,
  auto,
} from "@oai/artifact-tool";

import {
  Canvas,
} from "../node_modules/@oai/artifact-tool/node_modules/skia-canvas/lib/index.js";

import {
  drawSlideToCtx,
} from "@oai/artifact-tool";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..");
const projectRoot = path.resolve(workspaceRoot, "..", "..");

const outputDir = path.join(workspaceRoot, "output");
const scratchDir = path.join(workspaceRoot, "scratch");
const previewDir = path.join(scratchDir, "previews");
const assetDir = path.join(scratchDir, "assets");
const pptxPath = path.join(outputDir, "output.pptx");

const slideSize = { width: 1920, height: 1080 };

const colors = {
  ink: "#122033",
  muted: "#526173",
  accent: "#176B87",
  accentSoft: "#E7F3F7",
  positive: "#1F7A58",
  warn: "#B7791F",
  danger: "#A43E37",
  rule: "#D8E0E8",
  bg: "#F7F9FB",
};

const fonts = {
  title: { fontSize: 56, bold: true, color: colors.ink },
  subtitle: { fontSize: 24, color: colors.muted },
  section: { fontSize: 18, bold: true, color: colors.accent },
  body: { fontSize: 24, color: colors.ink },
  bodyMuted: { fontSize: 22, color: colors.muted },
  metric: { fontSize: 54, bold: true, color: colors.ink },
  metricLabel: { fontSize: 20, color: colors.muted },
  quote: { fontSize: 34, bold: true, color: colors.ink },
  footer: { fontSize: 12, color: colors.muted },
};

function bullets(items) {
  return items.map((item) => `• ${item}`).join("\n\n");
}

function smallBullets(items) {
  return items.map((item) => `• ${item}`).join("\n");
}

function footerText(source) {
  return source ? `Source: ${source}` : "";
}

function addStandardSlide(presentation, { title, subtitle, source, body }) {
  const slide = presentation.slides.add();
  slide.compose(
    grid(
      {
        name: "slide-root",
        width: fill,
        height: fill,
        columns: [fr(1)],
        rows: [auto, auto, fr(1), auto],
        rowGap: 18,
        padding: { x: 80, y: 60 },
      },
      [
        text(title, {
          name: "slide-title",
          width: wrap(1500),
          height: hug,
          style: fonts.title,
        }),
        text(subtitle, {
          name: "slide-subtitle",
          width: wrap(1480),
          height: hug,
          style: fonts.subtitle,
        }),
        body,
        text(footerText(source), {
          name: "source-rail",
          width: fill,
          height: hug,
          style: fonts.footer,
        }),
      ],
    ),
    {
      frame: { left: 0, top: 0, width: slideSize.width, height: slideSize.height },
      baseUnit: 8,
    },
  );
  return slide;
}

function metricBlock(value, label, emphasisColor = colors.ink) {
  return column(
    {
      name: `${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-metric`,
      width: fill,
      height: hug,
      gap: 6,
    },
    [
      text(value, {
        width: fill,
        height: hug,
        style: { ...fonts.metric, color: emphasisColor },
      }),
      text(label, {
        width: fill,
        height: hug,
        style: fonts.metricLabel,
      }),
    ],
  );
}

function imageNode(name, imagePath, heightPx, fit = "contain") {
  const source =
    typeof imagePath === "string" && imagePath.startsWith("data:")
      ? { dataUrl: imagePath }
      : { path: imagePath };
  return image({
    name,
    ...source,
    width: fill,
    height: fixed(heightPx),
    fit,
    alt: name,
  });
}

function recommendationRow(segment, objective, action, kpi) {
  return column(
    {
      width: fill,
      height: hug,
      gap: 12,
    },
    [
      row(
        {
          width: fill,
          height: hug,
          gap: 28,
        },
        [
          text(segment, {
            width: fixed(220),
            height: hug,
            style: { fontSize: 24, bold: true, color: colors.ink },
          }),
          text(objective, {
            width: fixed(420),
            height: hug,
            style: fonts.bodyMuted,
          }),
          text(action, {
            width: fixed(700),
            height: hug,
            style: fonts.body,
          }),
          text(kpi, {
            width: fill,
            height: hug,
            style: fonts.bodyMuted,
          }),
        ],
      ),
      rule({ width: fill, stroke: colors.rule, weight: 1 }),
    ],
  );
}

async function buildDeck() {
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });
  await fs.mkdir(assetDir, { recursive: true });

  const stageFigure = async (name) => {
    const source = path.join(projectRoot, "reports", "figures", name);
    const target = path.join(assetDir, name);
    await fs.copyFile(source, target);
    const bytes = await fs.readFile(target);
    return `data:image/png;base64,${bytes.toString("base64")}`;
  };

  const figures = {
    monthlyRevenueTrend: await stageFigure("monthly_revenue_trend.png"),
    dayOfWeekTrend: await stageFigure("day_of_week_trend.png"),
    hourOfDayTrend: await stageFigure("hour_of_day_trend.png"),
    cohortHeatmap: await stageFigure("cohort_retention_heatmap_optimized.png"),
    rfmRaw: await stageFigure("rfm_raw_distributions.png"),
    rfmLog: await stageFigure("rfm_log_distributions.png"),
    kmeansEval: await stageFigure("kmeans_optimal_k_evaluation.png"),
    clusterAverages: await stageFigure("cluster_averages_barchart.png"),
    clusterProfiles: await stageFigure("kmeans_cluster_profiles.png"),
    clusterSize: await stageFigure("cluster_size_distribution.png"),
  };

  const presentation = Presentation.create({ slideSize });

  const cover = presentation.slides.add();
  cover.compose(
    grid(
      {
        name: "cover-root",
        width: fill,
        height: fill,
        columns: [fr(0.58), fr(0.42)],
        rows: [auto, auto, fr(1), auto],
        columnGap: 56,
        rowGap: 18,
        padding: { x: 88, y: 72 },
      },
      [
        text("Customer Retention Intelligence", {
          name: "cover-title",
          width: wrap(920),
          height: hug,
          style: { fontSize: 66, bold: true, color: colors.ink },
        }),
        text("74.6%", {
          name: "cover-number",
          width: fill,
          height: hug,
          style: { fontSize: 160, bold: true, color: colors.accent },
        }),
        text("Business strategy, segmentation, churn scoring, and commercial recommendations drawn from the project notebooks and retained analysis outputs.", {
          name: "cover-subtitle",
          width: wrap(900),
          height: hug,
          style: { fontSize: 28, color: colors.muted },
        }),
        text("of revenue comes from the top 20% of customers, which makes retention precision more valuable than broad discounting.", {
          name: "cover-proof",
          width: wrap(620),
          height: hug,
          style: { fontSize: 28, color: colors.ink },
        }),
        column(
          {
            name: "cover-metrics",
            width: fill,
            height: hug,
            gap: 18,
          },
          [
            rule({ width: fixed(220), stroke: colors.accent, weight: 5 }),
            row({ width: fill, height: hug, gap: 28 }, [
              metricBlock("3,917", "customers profiled"),
              metricBlock("$8.88M", "known-customer revenue base"),
            ]),
            row({ width: fill, height: hug, gap: 28 }, [
              metricBlock("4", "operational customer clusters"),
              metricBlock("0.713", "final churn ROC-AUC"),
            ]),
          ],
        ),
        text("", {
          name: "cover-footer",
          width: wrap(640),
          height: hug,
          style: fonts.footer,
        }),
      ],
    ),
    {
      frame: { left: 0, top: 0, width: slideSize.width, height: slideSize.height },
      baseUnit: 8,
    },
  );

  addStandardSlide(presentation, {
    title: "Executive Summary",
    subtitle: "The analysis points to a concentrated customer base, fast early retention decay, and a need to prioritize high-value retention over broad win-back spending.",
    source: "eda.ipynb, rfm_analysis.ipynb, Segmentation.ipynb, churn_prediction.ipynb",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.52), fr(0.48)],
        columnGap: 40,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 24,
          },
          [
            text(bullets([
              "Top-customer concentration is high: the top 20% of customers generate 74.64% of revenue, so account protection should be a board-level KPI.",
              "Revenue seasonality is visible, with a strong run-up from September to November; retention and upsell campaigns should be staged before the peak, not during it.",
              "The largest segment is Lost/Inactive, but the biggest value pool sits inside Champions and Loyal Base, so intervention budgets should skew toward preservation and expansion.",
              "Cohort retention drops sharply after the first purchase month, which means second-order activation and early repeat behavior are the highest-leverage lifecycle moments.",
              "The churn model is useful for prioritization rather than automation. It is good enough to rank outreach and save-costs, but still needs monitored business rules.",
            ]), {
              name: "summary-bullets",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
        chart({
          name: "segment-value-pool-chart",
          chartType: "bar",
          width: fill,
          height: fill,
          config: {
            title: "Estimated Revenue Pool by Segment ($M)",
            categories: ["Champions", "Loyal Base", "Lost/Inactive", "Potential Loyals"],
            series: [
              {
                name: "Revenue pool ($M)",
                values: [4.54, 1.82, 0.48, 0.4],
              },
            ],
          },
        }),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Commercial Footprint and Revenue Concentration",
    subtitle: "The customer base is geographically broad, but commercially concentrated. That combination favors targeted retention motions and strong key-account discipline.",
    source: "eda.ipynb, reports/figures/monthly_revenue_trend.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.42), fr(0.58)],
        columnGap: 34,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            metricBlock("$8.88M", "known-customer revenue base"),
            metricBlock("37", "countries represented"),
            metricBlock("90.08%", "share of orders from the UK", colors.accent),
            metricBlock("74.64%", "revenue contribution from the top 20% of customers", colors.warn),
            text(smallBullets([
              "The UK remains the operating core, which makes domestic lifecycle optimization the fastest path to measurable impact.",
              "International demand exists, but order density is low enough that the first commercial focus should stay on the domestic base.",
              "Top-customer dependency means a small amount of churn among major accounts can wipe out gains from broad acquisition activity.",
            ]), {
              name: "footprint-notes",
              width: fill,
              height: hug,
              style: fonts.bodyMuted,
            }),
          ],
        ),
        imageNode("monthly-revenue-trend", figures.monthlyRevenueTrend, 720, "contain"),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Demand Rhythm and Campaign Timing",
    subtitle: "Ordering behavior is not flat through the week or the day. The operation already has natural engagement windows that marketing and CRM should exploit.",
    source: "eda.ipynb, reports/figures/day_of_week_trend.png, reports/figures/hour_of_day_trend.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.52), fr(0.48)],
        columnGap: 36,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 20,
          },
          [
            text(bullets([
              "Thursday is the strongest ordering day, followed by Wednesday and Tuesday, so midweek outbound campaigns should receive priority inventory and creative attention.",
              "The order peak lands between 10:00 and 14:00, with 12:00 as the highest-volume hour. Time-sensitive nudges should align to that window.",
              "The seasonal peak begins building in September and crests in November. That argues for pre-peak reactivation, replenishment, and loyalty messaging in late summer.",
              "Because weekend demand is structurally weaker, discount-led weekend pushes should be used selectively and only when stock or campaign objectives justify them.",
            ]), {
              name: "timing-bullets",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            imageNode("day-of-week-trend", figures.dayOfWeekTrend, 300, "contain"),
            imageNode("hour-of-day-trend", figures.hourOfDayTrend, 300, "contain"),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Retention Is Won in the First Few Months",
    subtitle: "The cohort heatmap shows sharp early drop-off and uneven long-run retention, which means first-to-second purchase conversion is the most important lifecycle moment to improve.",
    source: "rfm_analysis.ipynb, reports/figures/cohort_retention_heatmap_optimized.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.68), fr(0.32)],
        columnGap: 34,
      },
      [
        imageNode("cohort-retention-heatmap", figures.cohortHeatmap, 760, "contain"),
        column(
          {
            width: fill,
            height: fill,
            gap: 20,
          },
          [
            text("What the heatmap says", {
              width: fill,
              height: hug,
              style: fonts.section,
            }),
            text(bullets([
              "Month-two retention commonly lands in the high teens to mid-thirties rather than staying near the acquisition baseline.",
              "Stronger early cohorts can still hold roughly 30% to 50% retention deeper into their lifecycle, proving that better outcomes are achievable.",
              "The commercial opportunity is not only to win back old customers, but to stop newer cohorts from cooling off so quickly after the first order.",
            ]), {
              name: "cohort-callouts",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
            text("Recommended focus", {
              width: fill,
              height: hug,
              style: fonts.section,
            }),
            text(smallBullets([
              "second-purchase offers",
              "post-purchase replenishment journeys",
              "product-category based follow-ups within 30 to 60 days",
            ]), {
              name: "cohort-actions",
              width: fill,
              height: hug,
              style: fonts.bodyMuted,
            }),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "RFM Preparation Matters Because Customer Value Is Highly Skewed",
    subtitle: "The customer base is economically uneven. Without normalization, a small number of bulk buyers would dominate both segmentation and downstream model behavior.",
    source: "rfm_analysis.ipynb, reports/figures/rfm_raw_distributions.png, reports/figures/rfm_log_distributions.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.48), fr(0.52)],
        columnGap: 34,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            imageNode("rfm-raw-distributions", figures.rfmRaw, 250, "contain"),
            imageNode("rfm-log-distributions", figures.rfmLog, 250, "contain"),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 20,
          },
          [
            metricBlock("3,917", "customers in the RFM base"),
            metricBlock("$17.28k", "99th percentile monetary value"),
            metricBlock("$259.66k", "maximum single-customer monetary value", colors.warn),
            text(bullets([
              "Average monetary value is only $1,849, but the maximum customer value is more than fifteen times the 99th percentile.",
              "Median recency is 51 days and median frequency is 2 orders, which confirms that most customers are not habitually active.",
              "Log transforms are therefore not cosmetic; they are necessary to make clustering and scoring stable enough to support decisions.",
            ]), {
              name: "rfm-explanation",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Segmentation Was Chosen for Business Use, Not Only Statistical Purity",
    subtitle: "The clustering exercise shows the best silhouette at k=2, but the project adopts four clusters because that gives the business more usable operational groups.",
    source: "Segmentation.ipynb, reports/figures/kmeans_optimal_k_evaluation.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.58), fr(0.42)],
        columnGap: 34,
      },
      [
        imageNode("kmeans-optimal-k", figures.kmeansEval, 700, "contain"),
        column(
          {
            width: fill,
            height: fill,
            gap: 20,
          },
          [
            metricBlock("0.435", "silhouette score at k=2"),
            metricBlock("4", "chosen operational clusters", colors.accent),
            text(bullets([
              "The steep inertia decline from k=2 to k=4 suggests meaningful additional structure before returns diminish.",
              "Moving from 2 to 4 clusters trades some statistical compactness for better commercial granularity.",
              "That is a reasonable decision because retention teams need more than a binary split; they need distinct plays for protection, growth, nurture, and low-cost win-back.",
              "The final segmentation assigns all 3,917 customers into four interpretable groups.",
            ]), {
              name: "segmentation-choice",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Segment Behavior Is Economically Distinct",
    subtitle: "The cluster profile work shows that the segments are not just mathematically separable; they represent genuinely different economic behaviors and lifecycle states.",
    source: "Segmentation.ipynb, reports/figures/cluster_averages_barchart.png, reports/figures/kmeans_cluster_profiles.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(1)],
        rows: [auto, fr(1)],
        rowGap: 20,
      },
      [
        row(
          {
            width: fill,
            height: hug,
            gap: 24,
          },
          [
            text("Champions: 11.5-day recency, 13.7 orders, $7.2k average spend. These are the customers to protect aggressively.", {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
            text("Loyal Base: 68.3-day recency, 4.2 orders, $1.7k average spend. This is the upgrade pool with real expansion potential.", {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
            text("Potential Loyals: 19.2-day recency, 2.1 orders, $519 average spend. They are early-stage customers that need habit formation.", {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
            text("Lost/Inactive: 183.2-day recency, 1.3 orders, $331 average spend. They are numerous, but should be approached with cost discipline.", {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            imageNode("cluster-averages", figures.clusterAverages, 280, "contain"),
            imageNode("cluster-profiles", figures.clusterProfiles, 300, "contain"),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "The Largest Segment Is Not the Most Valuable Segment",
    subtitle: "Lost/Inactive customers form the biggest headcount block, but Champions and Loyal Base contain the majority of economic value. Budgeting should follow value, not just volume.",
    source: "Segmentation.ipynb, reports/figures/cluster_size_distribution.png",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.52), fr(0.48)],
        columnGap: 34,
      },
      [
        imageNode("cluster-size-distribution", figures.clusterSize, 720, "contain"),
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            text("Implication for spend allocation", {
              width: fill,
              height: hug,
              style: fonts.section,
            }),
            text(bullets([
              "Lost/Inactive contains 1,461 customers, but their combined value pool is only about $0.48M using average spend x customer count.",
              "Champions are only 630 customers, yet they represent an estimated $4.54M pool, making them the most important retention asset.",
              "Loyal Base adds another ~$1.82M pool and is the best segment for upsell, loyalty migration, and frequency-building tactics.",
              "Potential Loyals are smaller economically today, but they are the cheapest segment to shape through onboarding and second-order nudges.",
            ]), {
              name: "value-allocation-bullets",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
            text("Recommended budget split", {
              width: fill,
              height: hug,
              style: fonts.section,
            }),
            text(smallBullets([
              "Protect / expand Champions first",
              "Move Loyal Base toward Champion behavior second",
              "Nurture Potential Loyals through habit-building",
              "Keep Lost/Inactive win-back low-cost and tightly tested",
            ]), {
              name: "budget-split",
              width: fill,
              height: hug,
              style: fonts.bodyMuted,
            }),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "The Churn Model Is Directionally Useful and Operationally Practical",
    subtitle: "The final churn model adds RFM score features to the log-transformed base and improves ranking quality enough to support prioritization workflows.",
    source: "churn_prediction.ipynb",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.46), fr(0.54)],
        columnGap: 36,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            metricBlock("0.713", "final ROC-AUC", colors.accent),
            metricBlock("0.66", "final accuracy"),
            metricBlock("0.55", "recall on churned customers", colors.warn),
            metricBlock("+0.005", "ROC-AUC lift vs simpler feature set"),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 20,
          },
          [
            text("Business reading of model quality", {
              width: fill,
              height: hug,
              style: fonts.section,
            }),
            text(bullets([
              "This is a prioritization model, not a fully automated decision engine. It is strong enough to rank customers for intervention and suppress low-value blanket outreach.",
              "Class-1 recall around 0.55 means the model will miss some true churners, so it should sit inside a rules-based workflow rather than replace human judgement outright.",
              "Because the application also uses monetary value to assign intervention classes, the model is most useful when paired with commercial value thresholds.",
              "The operational sweet spot is to use the churn score to decide who receives expensive save motions, who receives nurture messaging, and who receives low-cost treatment only.",
            ]), {
              name: "churn-reading",
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "Recommended Segment Playbook",
    subtitle: "Retention strategy should be intentionally uneven. The right action depends on whether the segment carries near-term value, future potential, or low-return reactivation risk.",
    source: "eda.ipynb, rfm_analysis.ipynb, Segmentation.ipynb, churn_prediction.ipynb",
    body: column(
      {
        width: fill,
        height: fill,
        gap: 18,
      },
      [
        row(
          {
            width: fill,
            height: hug,
            gap: 28,
          },
          [
            text("Segment", { width: fixed(220), height: hug, style: fonts.section }),
            text("Commercial objective", { width: fixed(420), height: hug, style: fonts.section }),
            text("Recommended action", { width: fixed(700), height: hug, style: fonts.section }),
            text("Primary KPI", { width: fill, height: hug, style: fonts.section }),
          ],
        ),
        rule({ width: fill, stroke: colors.accent, weight: 2 }),
        recommendationRow(
          "Champions",
          "Protect revenue and defend relationship depth",
          "VIP treatment, early-access launches, replenishment reminders, concierge support, and churn-score based save outreach only when risk rises materially",
          "retention of top-value accounts, average order frequency",
        ),
        recommendationRow(
          "Loyal Base",
          "Increase frequency and basket depth",
          "Loyalty tiers, bundle offers, category cross-sell, and midweek re-engagement campaigns aligned to known order windows",
          "orders per customer, average basket size",
        ),
        recommendationRow(
          "Potential Loyals",
          "Convert into habitual repeat buyers",
          "second-purchase incentives, onboarding journeys, timed reminders within 30 to 60 days, and low-friction product education",
          "second-order conversion, 60-day repeat rate",
        ),
        recommendationRow(
          "Lost / Inactive",
          "Recover selectively without over-spending",
          "low-cost win-back tests, category-specific offers, suppression after non-response, and do-not-discount rules for chronically low-value profiles",
          "reactivation rate, cost per reactivated customer",
        ),
      ],
    ),
  });

  addStandardSlide(presentation, {
    title: "90-Day Implementation Plan",
    subtitle: "The project is ready to move from analysis into an operating decision layer. The first quarter should focus on campaign integration, measurement discipline, and controlled rollout.",
    source: "Project recommendation based on notebooks and deployed application behavior",
    body: grid(
      {
        width: fill,
        height: fill,
        columns: [fr(0.33), fr(0.33), fr(0.34)],
        columnGap: 28,
      },
      [
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            text("Days 1-30", { width: fill, height: hug, style: fonts.section }),
            text(bullets([
              "deploy the scoring app to Render or Railway",
              "finalize data refresh cadence for RFM inputs",
              "define business thresholds for Save, Protect, Maintain, and low-cost win-back",
              "launch dashboarding for churn score distribution, segment mix, and cohort retention",
            ]), {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            text("Days 31-60", { width: fill, height: hug, style: fonts.section }),
            text(bullets([
              "run targeted campaigns for Champions, Loyal Base, and Potential Loyals",
              "test low-cost win-back treatments on Lost/Inactive cohorts",
              "compare midweek and midday send windows against current campaign baselines",
              "measure second-order conversion and early repeat lift",
            ]), {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
        column(
          {
            width: fill,
            height: fill,
            gap: 18,
          },
          [
            text("Days 61-90", { width: fill, height: hug, style: fonts.section }),
            text(bullets([
              "review model lift by segment and customer value band",
              "tighten suppression rules for low-return reactivation attempts",
              "refresh the models if new performance data exposes drift",
              "turn the strongest interventions into standard CRM journeys before the next seasonal peak",
            ]), {
              width: fill,
              height: hug,
              style: fonts.body,
            }),
          ],
        ),
      ],
    ),
  });

  const pptxBlob = await PresentationFile.exportPptx(presentation);
  await pptxBlob.save(pptxPath);

  for (let index = 0; index < presentation.slides.items.length; index += 1) {
    const slide = presentation.slides.items[index];
    const canvas = new Canvas(slideSize.width, slideSize.height);
    const ctx = canvas.getContext("2d");
    await drawSlideToCtx(slide, presentation, ctx);
    const filePath = path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`);
    await canvas.toFile(filePath);
  }
}

await buildDeck();
