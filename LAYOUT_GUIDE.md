# Dashboard Layout Guide

Visual guide to the new adaptive dashboard layouts.

> **Note:** This guide covers widget positioning and layout strategies. For information about the visual spacer system that creates breathing room between sections, see **`SPACER_WIDGET_GUIDE.md`**.

---

## 🎯 **Counter Layouts**

### **1-2 Counters (Default Grid)**
```
┌────────┬────────┬────────┐
│ Filter │Counter │Counter │  y=0
│  (2x2) │   1    │   2    │
└────────┴────────┴────────┘
```

### **3 Counters (Single Row Below Filter)** ⭐ NEW
```
┌────────┐
│ Filter │  y=0
│  (2x2) │
├────────┼────────┬────────┐
│Counter │Counter │Counter │  y=2
│   1    │   2    │   3    │
└────────┴────────┴────────┘
```
- All 3 counters at same y-level (y=2)
- Positions: x=0, x=2, x=4
- Clean horizontal alignment

### **4+ Counters (Default Grid)**
```
┌────────┬────────┬────────┐
│ Filter │Counter │Counter │  y=0
│        │   1    │   2    │
├────────┼────────┼────────┤
│        │Counter │Counter │  y=2
│        │   3    │   4    │
└────────┴────────┴────────┘
```

---

## 📊 **Chart Layouts**

### **1 Chart (Full Width)**
```
┌─────────────────────────────┐
│                             │
│       Chart 1 (6x6)         │
│                             │
└─────────────────────────────┘
```

### **2 Charts (Side by Side)** ⭐
```
┌──────────────┬──────────────┐
│   Chart 1    │   Chart 2    │  y=current_y
│    (3x6)     │    (3x6)     │
└──────────────┴──────────────┘
```
- Both charts: Half width each
- Equal emphasis, side by side

### **3 Charts/Pivots (Hero + Split)** ⭐ NEW
```
┌─────────────────────────────┐
│                             │
│   Chart 1 - Hero (6x6)      │  y=current_y
│                             │
└─────────────────────────────┘
┌──────────────┬──────────────┐
│   Chart 2    │   Chart 3    │  y=current_y+6
│    (3x6)     │ or Pivot (3x6│
└──────────────┴──────────────┘
```
- First chart: Full width (hero)
- Other 2: Split width below

### **4+ Charts (Standard Grid)**
```
┌──────────────┬──────────────┐
│   Chart 1    │   Chart 2    │
│    (3x6)     │    (3x6)     │
├──────────────┼──────────────┤
│   Chart 3    │   Chart 4    │
│    (3x6)     │    (3x6)     │
└──────────────┴──────────────┘
```
- 2 per row (standard grid)

---

## 📋 **Complete Dashboard Examples**

### **Example 1: Filter + 3 Counters + 2 Charts**
```
┌────────┐                      y=0
│ Filter │
│  (2x2) │
├────────┼────────┬────────┐    y=2
│Counter │Counter │Counter │
│   1    │   2    │   3    │
├────────┴────────┴────────┤    y=4
│  Bar Chart  │ Line Chart │
│    (3x6)    │   (3x6)    │
└─────────────┴────────────┘
```

### **Example 2: Filter + 2 Counters + 2 Charts + Table** (with spacers)
```
┌────────┬────────┬────────┐    y=0
│ Filter │Counter │Counter │
│  (2x2) │   1    │   2    │
└────────┴────────┴────────┘
═══════════════════════════     y=2  ← SPACER (h=1)
┌──────────────┬────────────┐   y=3
│  Bar Chart   │ Line Chart │
│    (3x6)     │   (3x6)    │
└──────────────┴────────────┘
═══════════════════════════     y=9  ← SPACER (h=1)
┌───────────────────────────┐   y=10
│                           │
│    Table (full width)     │
│                           │
└───────────────────────────┘
```
Note: Spacers add visual breathing room between sections (see `SPACER_WIDGET_GUIDE.md`)

### **Example 3: Filter + 3 Counters + Bar + Line + Pivot**
```
┌────────┐                      y=0
│ Filter │
│  (2x2) │
├────────┼────────┬────────┐    y=2
│Counter │Counter │Counter │
│   1    │   2    │   3    │
├────────┴────────┴────────┤    y=4
│                           │
│   Bar Chart - Hero (6x6)  │
│                           │
├──────────────┬────────────┤    y=10
│  Line Chart  │   Pivot    │
│    (3x6)     │   (3x6)    │
└──────────────┴────────────┘
```

---

## 🎨 **Design Principles Applied**

### ✅ **Visual Comfort**
- Hero layouts reduce visual density
- Clear focal point (first chart emphasized)
- Better balance with asymmetric layouts

### ✅ **Information Hierarchy**
- **Top**: Filter + KPIs (what matters most)
- **Middle**: Hero chart (primary insight) + supporting charts
- **Bottom**: Details (tables, pivots)

### ✅ **Eye Scanning Pattern**
- Left-to-right: Filter → Counters
- Top-to-bottom: KPIs → Main chart → Supporting charts → Details
- Natural F-pattern reading flow

### ✅ **Flexibility**
- 1 chart: Full width (maximum impact)
- 2 charts: Side by side (comparison, equal emphasis)
- 3 charts: Hero layout (primary + supporting)
- 4+ charts: Grid layout (equal emphasis)

---

## 🔢 **Layout Decision Matrix**

| Counters | Charts | Layout Strategy |
|----------|--------|-----------------|
| 1-2 | Any | Counters in grid (2 per row) |
| **3** | Any | **All counters in single row (y=2)** ⭐ |
| 4+ | Any | Counters in grid (2 per row) |
| Any | 1 | Chart full width |
| Any | **2** | **Side by side (equal width)** ⭐ |
| Any | **3** | **Hero layout (1 full + 2 split)** ⭐ |
| Any | 4+ | Standard grid (2 per row) |

---

## 💡 **Why These Layouts?**

### **3 Counters in One Row:**
- Visual symmetry: 3 equal boxes
- Avoids awkward 2+1 split
- Better use of horizontal space
- More professional appearance

### **2 Charts Side by Side:**
- Equal emphasis for comparison
- Efficient use of horizontal space
- Easy to compare insights
- Clean, balanced appearance

### **Hero Chart Layout (3 charts only):**
- Emphasizes the most important chart (first one)
- Reduces visual weight
- Creates focal point
- Better storytelling (main insight + supporting details)
- More engaging than uniform grid

### **Standard Grid (4+ charts):**
- Equal emphasis when many metrics matter
- Predictable pattern
- Space efficient

---

## 📐 **Grid Reference**

Dashboard grid is **6 units wide**:
- Each unit = 1/6 of total width
- Filter: 2 units (33%)
- Counter: 2 units (33%)
- Half chart: 3 units (50%)
- Full chart: 6 units (100%)

**Heights:**
- Filter/Counter: 2 units
- Charts: 6 units
- Table: 8 units

---

**Summary:** The new layouts create more visually comfortable, hierarchically clear dashboards that guide the user's attention naturally from KPIs → Main insights → Supporting details → Detailed data. 🎯

