let students = [];
let absentStudentIds = new Set();
let currentSession = "morning";
let currentDayType = "working";
let currentOccasionName = "";
let hasCurrentAttendanceRecords = false;

document.addEventListener("DOMContentLoaded", function () {
    const dateInput = document.getElementById("attendanceDate");
    if (dateInput) {
        dateInput.addEventListener("change", function () {
            loadAttendanceData();
        });
    }

    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("input", function (e) {
            filterStudentTable(e.target.value.toLowerCase());
        });
    }

    // Initial Load
    loadAttendanceData();
});

// Switch Session: Morning or Afternoon
function switchSession(sessionType) {
    currentSession = sessionType;
    const btnMorning = document.getElementById("btnMorning");
    const btnAfternoon = document.getElementById("btnAfternoon");
    const sessionNotice = document.getElementById("sessionNotice");

    if (sessionType === "morning") {
        btnMorning.classList.add("active", "morning");
        btnAfternoon.classList.remove("active", "afternoon");
        if (sessionNotice) sessionNotice.innerHTML = `<i class="bi bi-sun-fill text-warning me-1"></i> Morning`;
    } else {
        btnAfternoon.classList.add("active", "afternoon");
        btnMorning.classList.remove("active", "morning");
        if (sessionNotice) sessionNotice.innerHTML = `<i class="bi bi-cloud-sun-fill text-danger me-1"></i> Afternoon`;
    }

    loadAttendanceData();
}

// Day Type Dropdown Change Handler
function onDayTypeChange() {
    const select = document.getElementById("dayTypeSelect");
    const chosenType = select.value;

    if (chosenType === "holiday") {
        // Open modal to get occasion name
        document.getElementById("occasionInput").value = currentOccasionName || "";
        const modal = new bootstrap.Modal(document.getElementById("occasionModal"));
        modal.show();
    } else {
        currentDayType = chosenType;
        currentOccasionName = "";
        applyDayTypeUI();
        autoSaveDayStatus();
    }
}

// Confirm Holiday Occasion
function confirmHolidayOccasion() {
    const occasion = document.getElementById("occasionInput").value.trim();
    if (!occasion) {
        alert("Please enter the occasion or festival name (e.g. Sankranti, Diwali, Gandhi Jayanti)!");
        return;
    }

    currentDayType = "holiday";
    currentOccasionName = occasion;

    const modalEl = document.getElementById("occasionModal");
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) modalInstance.hide();

    applyDayTypeUI();
    autoSaveDayStatus();
}

function cancelHolidayModal() {
    const modalEl = document.getElementById("occasionModal");
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) modalInstance.hide();

    // Revert select back to working if not previously holiday
    if (currentDayType !== "holiday") {
        document.getElementById("dayTypeSelect").value = currentDayType;
    }
}

function editHolidayOccasion() {
    document.getElementById("occasionInput").value = currentOccasionName || "";
    const modal = new bootstrap.Modal(document.getElementById("occasionModal"));
    modal.show();
}

// Automatically save day status change to server
async function autoSaveDayStatus() {
    const dateVal = document.getElementById("attendanceDate").value;
    try {
        await fetch("/api/save-day-status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                date: dateVal,
                day_type: currentDayType,
                occasion_name: currentOccasionName
            })
        });
    } catch (err) {
        console.error("Error updating day status:", err);
    }
}

// Apply Day Type UI Visual State
function applyDayTypeUI() {
    const banner = document.getElementById("holidayBanner");
    const bannerTitle = document.getElementById("holidayBannerTitle");
    const bannerDesc = document.getElementById("holidayBannerDesc");
    const tableControls = document.getElementById("tableControlsCol");
    const btnParents = document.getElementById("btnParentsWhatsApp");
    const daySelect = document.getElementById("dayTypeSelect");
    const tableSubTitle = document.getElementById("tableCardSubTitle");

    daySelect.value = currentDayType;

    if (currentDayType === "working") {
        banner.style.display = "none";
        if (tableControls) tableControls.style.display = "block";
        if (btnParents) btnParents.disabled = false;
        if (tableSubTitle) tableSubTitle.innerHTML = "Click <b>[P]</b> for Present or <b>[A]</b> for Absent. Or type roll numbers in Quick Absent box.";
    } else {
        banner.style.display = "block";
        if (tableControls) tableControls.style.display = "none";
        if (btnParents) btnParents.disabled = true;

        if (currentDayType === "sunday") {
            bannerTitle.innerHTML = `<i class="bi bi-sun-fill text-warning me-2"></i> Sunday (Weekly College Off)`;
            bannerDesc.innerText = "College is closed for the weekly Sunday holiday. Absence notifications are disabled. You can still select prior dates to review past attendance.";
            if (tableSubTitle) tableSubTitle.innerText = "Sunday observed. Attendance marking is inactive.";
        } else if (currentDayType === "second_saturday") {
            bannerTitle.innerHTML = `<i class="bi bi-building-slash text-warning me-2"></i> Second Saturday (Official College Holiday)`;
            bannerDesc.innerText = "College is closed for the 2nd Saturday holiday. Absence notifications are paused.";
            if (tableSubTitle) tableSubTitle.innerText = "Second Saturday observed. Attendance marking is inactive.";
        } else if (currentDayType === "holiday") {
            bannerTitle.innerHTML = `<i class="bi bi-flag-fill text-danger me-2"></i> Declared Holiday: ${currentOccasionName || 'College Holiday'}`;
            bannerDesc.innerText = `College is closed on account of "${currentOccasionName || 'Holiday'}". Absence alerts are disabled.`;
            if (tableSubTitle) tableSubTitle.innerText = `Holiday observed (${currentOccasionName}). Attendance marking is inactive.`;
        }
    }

    renderStudentTable();
    updateStatistics();
}

// Fetch Students & Saved Attendance for Date and Session
async function loadAttendanceData() {
    const dateVal = document.getElementById("attendanceDate").value;
    const tableBody = document.getElementById("studentTableBody");
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading student records...
            </td>
        </tr>
    `;

    try {
        const response = await fetch(`/api/students?date=${dateVal}&session=${currentSession}`);
        if (response.status === 401) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger py-4">
                        <i class="bi bi-shield-lock-fill me-1"></i> Your login session has expired. 
                        <a href="/login" class="btn btn-sm btn-primary ms-2 fw-bold"><i class="bi bi-box-arrow-in-right me-1"></i> Sign In Again</a>
                    </td>
                </tr>
            `;
            return;
        }

        const data = await response.json();

        if (data.status === "success") {
            students = data.students;
            absentStudentIds.clear();

            currentDayType = data.day_type || "working";
            currentOccasionName = data.occasion_name || "";
            hasCurrentAttendanceRecords = !!data.has_attendance_records;

            // If working day, populate absentees
            if (currentDayType === "working") {
                data.absent_ids.forEach(id => absentStudentIds.add(id));
            }

            applyDayTypeUI();

            // Update in-page status indicator
            const statusIndicator = document.getElementById("saveStatusIndicator");
            if (statusIndicator) {
                if (hasCurrentAttendanceRecords) {
                    statusIndicator.className = "badge bg-success-subtle text-success border border-success px-3 py-2 align-self-center small d-none d-lg-inline-block";
                    statusIndicator.innerHTML = `<i class="bi bi-database-check text-success me-1"></i> Stored in DB (${absentStudentIds.size} Absentees)`;
                } else {
                    statusIndicator.className = "badge bg-warning-subtle text-warning-emphasis border border-warning px-3 py-2 align-self-center small d-none d-lg-inline-block";
                    statusIndicator.innerHTML = `<i class="bi bi-clock-history me-1"></i> Attendance Pending (Not Yet Saved)`;
                }
            }

            const unmarkedNotice = document.getElementById("unmarkedNotice");
            if (unmarkedNotice) {
                unmarkedNotice.style.display = (currentDayType === "working" && !hasCurrentAttendanceRecords) ? "flex" : "none";
            }
        } else {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">${data.message}</td></tr>`;
        }
    } catch (err) {
        console.error("Error loading students:", err);
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Failed to load student data.</td></tr>`;
    }
}

// Render Student Table with Modern [ P | A ] Segmented Switch
function renderStudentTable(filteredStudents = null) {
    const list = filteredStudents || students;
    const tableBody = document.getElementById("studentTableBody");

    if (list.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    No student records found in this section.
                </td>
            </tr>
        `;
        return;
    }

    let html = "";
    const isHoliday = currentDayType !== "working";

    list.forEach((s, idx) => {
        const isAbsent = !isHoliday && absentStudentIds.has(s.id);
        const rowClass = isHoliday ? "table-light text-muted" : (isAbsent ? "row-absent" : "");
        
        let statusBadge = "";
        if (isHoliday) {
            statusBadge = `<span class="badge bg-secondary px-2 py-1"><i class="bi bi-calendar-x me-1"></i>HOLIDAY</span>`;
        } else if (isAbsent) {
            statusBadge = `<span class="badge badge-absent-pill px-2.5 py-1.5 shadow-sm"><i class="bi bi-x-circle-fill me-1"></i>ABSENT</span>`;
        } else {
            statusBadge = `<span class="badge badge-present-pill px-2.5 py-1.5 shadow-sm"><i class="bi bi-check-circle-fill me-1"></i>PRESENT</span>`;
        }

        const toggleHtml = isHoliday 
            ? `<span class="badge bg-light text-muted border">OFF</span>`
            : `
                <div class="attendance-toggle-pill" role="group" aria-label="Attendance">
                    <button type="button" class="btn-att-toggle ${!isAbsent ? 'active-p' : ''}" onclick="event.stopPropagation(); setStudentStatus(${s.id}, 'present')" title="Mark ${s.name} Present">
                        <i class="bi bi-check-circle-fill me-1"></i>P
                    </button>
                    <button type="button" class="btn-att-toggle ${isAbsent ? 'active-a' : ''}" onclick="event.stopPropagation(); setStudentStatus(${s.id}, 'absent')" title="Mark ${s.name} Absent">
                        <i class="bi bi-x-circle-fill me-1"></i>A
                    </button>
                </div>
            `;

        html += `
            <tr class="${rowClass}" id="student-row-${s.id}" style="cursor: pointer;" onclick="toggleStudentStatus(${s.id})">
                <td class="text-center" id="toggle-cell-${s.id}" onclick="event.stopPropagation()">
                    ${toggleHtml}
                </td>
                <td><small class="text-muted fw-bold">${idx + 1}</small></td>
                <td><strong class="text-primary">${s.roll_number}</strong></td>
                <td class="fw-semibold">${s.name}</td>
                <td class="text-muted">${s.father_name}</td>
                <td onclick="event.stopPropagation()">
                    <a href="https://wa.me/91${s.father_phone}" target="_blank" class="btn btn-sm btn-student-wa py-1 px-2 text-decoration-none" title="Direct WhatsApp Chat">
                        <i class="bi bi-whatsapp me-1 text-success"></i> +91 ${s.father_phone}
                    </a>
                </td>
                <td class="text-center" id="status-cell-${s.id}">
                    ${statusBadge}
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

let autoSaveDebounceTimer = null;
function triggerAutoSave() {
    const statusIndicator = document.getElementById("saveStatusIndicator");
    if (statusIndicator) {
        statusIndicator.className = "badge badge-db-status bg-info-subtle text-primary border border-info px-3 py-2";
        statusIndicator.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Auto-saving...`;
    }
    clearTimeout(autoSaveDebounceTimer);
    autoSaveDebounceTimer = setTimeout(() => {
        saveAttendanceData(true);
    }, 1200);
}

// Explicitly set student status to 'present' or 'absent'
function setStudentStatus(studentId, status) {
    if (currentDayType !== "working") return;

    if (status === "absent") {
        absentStudentIds.add(studentId);
    } else {
        absentStudentIds.delete(studentId);
    }

    const row = document.getElementById(`student-row-${studentId}`);
    const statusCell = document.getElementById(`status-cell-${studentId}`);
    const toggleCell = document.getElementById(`toggle-cell-${studentId}`);
    const isAbsent = absentStudentIds.has(studentId);

    if (row && statusCell) {
        if (isAbsent) {
            row.classList.add("row-absent");
            statusCell.innerHTML = `<span class="badge badge-absent-pill px-2.5 py-1.5 shadow-sm"><i class="bi bi-x-circle-fill me-1"></i>ABSENT</span>`;
        } else {
            row.classList.remove("row-absent");
            statusCell.innerHTML = `<span class="badge badge-present-pill px-2.5 py-1.5 shadow-sm"><i class="bi bi-check-circle-fill me-1"></i>PRESENT</span>`;
        }
    }

    if (toggleCell) {
        toggleCell.innerHTML = `
            <div class="attendance-toggle-pill" role="group" aria-label="Attendance">
                <button type="button" class="btn-att-toggle ${!isAbsent ? 'active-p' : ''}" onclick="event.stopPropagation(); setStudentStatus(${studentId}, 'present')" title="Mark Present">
                    <i class="bi bi-check-circle-fill me-1"></i>P
                </button>
                <button type="button" class="btn-att-toggle ${isAbsent ? 'active-a' : ''}" onclick="event.stopPropagation(); setStudentStatus(${studentId}, 'absent')" title="Mark Absent">
                    <i class="bi bi-x-circle-fill me-1"></i>A
                </button>
            </div>
        `;
    }

    const unmarkedNotice = document.getElementById("unmarkedNotice");
    if (unmarkedNotice) unmarkedNotice.style.display = "none";

    updateStatistics();
    triggerAutoSave();
}

// Toggle individual student absent/present state
function toggleStudentStatus(studentId) {
    if (currentDayType !== "working") return;
    if (absentStudentIds.has(studentId)) {
        setStudentStatus(studentId, 'present');
    } else {
        setStudentStatus(studentId, 'absent');
    }
}

// Backward compatibility alias for toggleAbsent
function toggleAbsent(studentId) {
    toggleStudentStatus(studentId);
}

// Quick Absent Entry by typing roll numbers (e.g. 5, 12, 43)
function quickMarkAbsent() {
    const input = document.getElementById("quickAbsentInput");
    if (!input || !input.value.trim()) return;

    const raw = input.value.trim();
    const tokens = raw.split(/[,\s]+/).map(t => t.trim()).filter(Boolean);
    if (tokens.length === 0) return;

    let matchedCount = 0;
    const matchedList = [];

    tokens.forEach(tok => {
        const cleanTok = tok.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
        students.forEach(s => {
            const cleanRoll = (s.roll_number || '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
            const isMatch = (cleanRoll === cleanTok) || 
                           cleanRoll.endsWith(cleanTok) || 
                           (cleanTok.length <= 3 && cleanRoll.endsWith(cleanTok.padStart(2, '0')));
            if (isMatch && !absentStudentIds.has(s.id)) {
                absentStudentIds.add(s.id);
                matchedCount++;
                matchedList.push(`${s.roll_number} - ${s.name}`);
            }
        });
    });

    input.value = "";
    renderStudentTable();
    updateStatistics();
    triggerAutoSave();

    const unmarkedNotice = document.getElementById("unmarkedNotice");
    if (unmarkedNotice) unmarkedNotice.style.display = "none";

    if (matchedCount > 0) {
        alert(`🔴 Marked ${matchedCount} student(s) as ABSENT:\n\n` + matchedList.join("\n"));
    } else {
        alert(`⚠️ No matching students found for: "${raw}".\nPlease check the roll numbers.`);
    }
}

// Mark All Absent or Clear All (All Present)
function toggleAllAbsent(markAll) {
    if (currentDayType !== "working") return;

    if (markAll) {
        students.forEach(s => absentStudentIds.add(s.id));
    } else {
        absentStudentIds.clear();
    }

    const unmarkedNotice = document.getElementById("unmarkedNotice");
    if (unmarkedNotice) unmarkedNotice.style.display = "none";

    renderStudentTable();
    updateStatistics();
    triggerAutoSave();
}

// Update Counters & Percentages (Accurate Daily Attendance Calculation)
function updateStatistics() {
    const total = students.length;
    const statTotalEl = document.getElementById("statTotal");
    const statPresentEl = document.getElementById("statPresent");
    const statAbsentEl = document.getElementById("statAbsent");
    const statPercentageEl = document.getElementById("statPercentage");
    const barAbsent = document.getElementById("barAbsentCount");
    const barBadge = document.getElementById("barBadge");

    statTotalEl.innerText = total;

    if (currentDayType !== "working") {
        // Holiday Calculations
        statPresentEl.innerText = "0";
        statAbsentEl.innerText = "0";
        statPercentageEl.innerText = "HOLIDAY";
        if (barAbsent) barAbsent.innerText = "0";
        if (barBadge) {
            barBadge.className = "badge bg-secondary fs-6 px-2 px-md-3 py-2";
            barBadge.innerHTML = `<i class="bi bi-calendar-x me-1"></i> Holiday`;
        }
    } else {
        // Working Day Calculations
        const absent = absentStudentIds.size;
        const present = total - absent;
        const percentage = total > 0 ? ((present / total) * 100).toFixed(1) : 0;

        statPresentEl.innerText = present;
        statAbsentEl.innerText = absent;
        statPercentageEl.innerText = `${percentage}%`;
        if (barAbsent) barAbsent.innerText = absent;
        if (barBadge) {
            barBadge.className = "badge badge-absent-glow fs-6 px-2 px-md-3 py-2";
            barBadge.innerHTML = `<i class="bi bi-bell-fill me-1 bell-icon-anim"></i> <span id="barAbsentCount">${absent}</span> Absentees`;
        }
    }
}

// Filter students by Search Query
function filterStudentTable(query) {
    if (!query) {
        renderStudentTable();
        return;
    }
    const filtered = students.filter(s =>
        s.roll_number.toLowerCase().includes(query) ||
        s.name.toLowerCase().includes(query) ||
        s.father_name.toLowerCase().includes(query) ||
        s.father_phone.includes(query)
    );
    renderStudentTable(filtered);
}

function getDeviceGpsCoordinates() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ lat: null, lng: null });
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
            (err) => resolve({ lat: null, lng: null, error: err.message }),
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 15000 }
        );
    });
}

function retryAttendanceWithLocation() {
    const modalEl = document.getElementById("geofenceAlertModal");
    if (modalEl && typeof bootstrap !== 'undefined') {
        bootstrap.Modal.getInstance(modalEl)?.hide();
    }
    saveAttendanceData(false);
}

function submitAttendanceWithBypass() {
    const bypassInput = document.getElementById("geofenceBypassInput");
    const bypassVal = (bypassInput ? bypassInput.value : "").trim();
    if (!bypassVal) {
        alert("Please enter the emergency bypass passkey provided by the Administrator.");
        return;
    }
    saveAttendanceData(false, bypassVal);
}

// Save Attendance to Database (supports silent auto-save and campus geo-fencing)
async function saveAttendanceData(silent = false, bypassKey = null) {
    const dateVal = document.getElementById("attendanceDate").value;

    // Accidental Save Prevention: Confirm if 0 absentees are marked and attendance is pending
    if (!silent && absentStudentIds.size === 0 && !hasCurrentAttendanceRecords) {
        const confirmed = confirm(`⚠️ ATTENDANCE CONFIRMATION (100% Present)\n\nAre you sure ALL ${students.length} students in this class are PRESENT today for the ${currentSession.toUpperCase()} session?\n\n• Click [OK] if no student is absent (Full Class Present).\n• Click [Cancel] to check the roll sheet and mark absentees.`);
        if (!confirmed) {
            return;
        }
    }

    const btnSave = document.getElementById("btnSaveAttendance");
    const originalText = btnSave ? btnSave.innerHTML : "";
    if (btnSave && !silent) {
        btnSave.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Saving...`;
        btnSave.disabled = true;
    }

    let coords = { lat: null, lng: null };
    if (!bypassKey && navigator.geolocation) {
        try {
            coords = await getDeviceGpsCoordinates();
        } catch (e) {
            console.warn("Could not retrieve GPS coordinates:", e);
        }
    }

    const payload = {
        date: dateVal,
        session: currentSession,
        absent_ids: Array.from(absentStudentIds),
        day_type: currentDayType,
        occasion_name: currentOccasionName,
        latitude: coords.lat,
        longitude: coords.lng
    };

    if (bypassKey) {
        payload.bypass_key = bypassKey;
    }

    try {
        const res = await fetch("/api/save-attendance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.status === 401) {
            alert("⚠️ Your login session has expired. Please sign in again to save attendance.");
            window.location.href = "/login";
            return;
        }

        const result = await res.json();

        if (result.is_geofence_error) {
            const modalEl = document.getElementById("geofenceAlertModal");
            if (modalEl && typeof bootstrap !== 'undefined') {
                const msgEl = document.getElementById("geofenceAlertMessage");
                const radEl = document.getElementById("geofenceAllowedRadius");
                const distEl = document.getElementById("geofenceDetectedDistance");
                if (msgEl) msgEl.innerText = result.message || "Attendance submission requires being on SSITS campus premises.";
                if (radEl) radEl.innerText = (result.allowed_radius ? Math.round(result.allowed_radius) + " meters" : "1000 meters");
                if (distEl) distEl.innerText = (result.distance_meters ? Math.round(result.distance_meters) + " meters" : "GPS coordinates unavailable");
                bootstrap.Modal.getOrCreateInstance(modalEl).show();
            } else {
                alert(result.message || "Campus Geo-Fencing is active: You must be on college premises to submit attendance.");
            }
            return;
        }

        if (result.status === "success") {
            hasCurrentAttendanceRecords = true;
            const alertModalEl = document.getElementById("geofenceAlertModal");
            if (alertModalEl && typeof bootstrap !== 'undefined') {
                bootstrap.Modal.getInstance(alertModalEl)?.hide();
            }

            const now = new Date();
            const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

            // Update in-page status badge
            const statusIndicator = document.getElementById("saveStatusIndicator");
            if (statusIndicator) {
                statusIndicator.className = "badge badge-db-status px-2 py-2 bg-success-subtle text-success border border-success";
                statusIndicator.innerHTML = `<i class="bi bi-check-circle-fill text-success me-1"></i> All Saved to DB (${timeStr})`;
            }

            if (!silent) {
                // Populate Modal details
                const modalDateSession = document.getElementById("modalSaveDateSession");
                const modalTimestamp = document.getElementById("modalSaveTimestamp");
                const modalTotal = document.getElementById("modalSaveTotal");
                const modalPresent = document.getElementById("modalSavePresent");
                const modalAbsent = document.getElementById("modalSaveAbsent");

                if (modalDateSession) modalDateSession.innerText = `${dateVal} (${currentSession.toUpperCase()})`;
                if (modalTimestamp) modalTimestamp.innerText = timeStr;
                if (modalTotal) modalTotal.innerText = students.length;
                if (modalPresent) modalPresent.innerText = currentDayType === "working" ? (students.length - absentStudentIds.size) : 0;
                if (modalAbsent) modalAbsent.innerText = currentDayType === "working" ? absentStudentIds.size : 0;

                const modalEl = document.getElementById("saveConfirmModal");
                if (modalEl && typeof bootstrap !== 'undefined') {
                    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                    modal.show();
                } else {
                    alert(`Attendance successfully saved to database for ${dateVal} (${currentSession.toUpperCase()})!`);
                }
            }
        } else if (!silent) {
            alert(`Failed to save: ${result.message}`);
        }
    } catch (err) {
        console.error("Save error:", err);
        if (!silent) alert("Error saving attendance to server.");
    } finally {
        if (btnSave && !silent) {
            btnSave.innerHTML = originalText;
            btnSave.disabled = false;
        }
    }
}

// Generate Combined WhatsApp Message for a Parent (Single Chat, Single Message)
function createParentWhatsAppMessage(student) {
    const dateVal = document.getElementById("attendanceDate").value;
    const sessionTextEng = currentSession === "morning" ? "Morning Session" : "Afternoon Session (Post-Lunch / Bunk)";
    const sessionTextTel = currentSession === "morning" ? "ఉదయం (Morning) సెషన్" : "మధ్యాహ్నం (Afternoon) సెషన్";

    return `🚨 *SRI SAI INSTITUTE OF TECHNOLOGY AND SCIENCE* 🚨
(AN AUTONOMOUS INSTITUTION | Approved by AICTE, Affiliated to JNTUA, Accredited by NAAC 'B+' Grade)

*ATTENDANCE ALERT - ABSENT NOTIFICATION*
--------------------------------------------------
Dear Parent (Sri/Smt. *${student.father_name}*),
This is to inform you that your ward *${student.name}* (Roll No: *${student.roll_number}*), Program: *${window.PROGRAM_NAME}*, Branch: *${window.DEPT_CODE}* (${window.YEAR_NAME}) is marked *ABSENT* today (*${dateVal}*) for the *${sessionTextEng}*.

మీ అబ్బాయి/అమ్మాయి *${student.name}* (రోల్ నెం: *${student.roll_number}*) ఈరోజు (*${dateVal}*) *${sessionTextTel}* కాలేజీకి రాలేదు (ABSENT). దయచేసి గమనించగలరు.
--------------------------------------------------

👨‍🏫 Class Teacher: *${window.TEACHER_NAME}*
📞 Contact Phone: *${window.TEACHER_PHONE}*
🏛️ *Sri Sai Institute of Technology and Science*`.trim();
}

// Open WhatsApp Modal for Parents
async function openWhatsAppModal() {
    if (currentDayType !== "working") {
        alert("Cannot send parent absence alerts on Sundays, Second Saturdays, or Holidays!");
        return;
    }

    // Always commit marked attendance to Central SQLite DB first!
    await saveAttendanceData(true);

    const modalList = document.getElementById("absenteeParentList");
    const absentList = students.filter(s => absentStudentIds.has(s.id));

    if (absentList.length === 0) {
        alert("No students are marked absent for this session (100% Attendance).");
        return;
    }

    let html = "";
    absentList.forEach((s, index) => {
        const msg = createParentWhatsAppMessage(s);
        const encodedMsg = encodeURIComponent(msg);
        const waLink = `https://wa.me/91${s.father_phone}?text=${encodedMsg}`;

        html += `
            <div class="card p-3 border shadow-sm">
                <div class="row align-items-center g-2">
                    <div class="col-12 col-md-7">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-danger me-2 fs-6">${index + 1}</span>
                            <div>
                                <h6 class="fw-bold mb-0 text-navy">${s.name} <span class="badge bg-secondary">${s.roll_number}</span></h6>
                                <div class="small text-muted">
                                    Parent: <strong>${s.father_name}</strong> | 
                                    WhatsApp: <strong class="text-success">+91 ${s.father_phone}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-12 col-md-5 text-md-end">
                        <div class="d-flex gap-2 justify-content-md-end">
                            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard(\`${encodeURIComponent(msg)}\`)">
                                <i class="bi bi-clipboard me-1"></i> Copy Message
                            </button>
                            <a href="${waLink}" target="_blank" class="btn btn-sm btn-whatsapp">
                                <i class="bi bi-whatsapp me-1"></i> Send WhatsApp
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    modalList.innerHTML = html;
    const modal = new bootstrap.Modal(document.getElementById("whatsAppModal"));
    modal.show();
}

function copyToClipboard(encodedText) {
    const text = decodeURIComponent(encodedText);
    navigator.clipboard.writeText(text).then(() => {
        alert("WhatsApp message copied to clipboard!");
    }).catch(err => {
        console.error("Clipboard copy error:", err);
    });
}

// Generate HOD Summary WhatsApp Message
function generateHodSummaryMessage() {
    const dateVal = document.getElementById("attendanceDate").value;
    const sessionLabel = currentSession === "morning" ? "Morning Session" : "Afternoon Session (Post-Lunch / Bunk)";
    const total = students.length;

    if (currentDayType !== "working") {
        let reason = currentDayType === "sunday" ? "Sunday (Weekly Off)" : (currentDayType === "second_saturday" ? "Second Saturday" : `Holiday (${currentOccasionName})`);
        return `📊 *SSITS - DAILY ATTENDANCE SUMMARY REPORT* 📊
---------------------------------------------
🏛️ *Institution:* Sri Sai Institute of Technology & Science
🎓 *Program:* ${window.PROGRAM_NAME}
📌 *Department:* ${window.DEPT_NAME} (${window.DEPT_CODE})
📅 *Class:* ${window.YEAR_NAME}
📆 *Date:* ${dateVal}
👨‍🏫 *Class Teacher:* ${window.TEACHER_NAME}
---------------------------------------------
🌴 *STATUS: COLLEGE HOLIDAY OBSERVED*
📌 *Occasion:* ${reason}
📈 *Total Strength:* ${total}
*Note: No regular classes conducted. No absence recorded.*`.trim();
    }

    const absentCount = absentStudentIds.size;
    const present = total - absentCount;
    const pct = total > 0 ? ((present / total) * 100).toFixed(1) : 0;

    const absentees = students.filter(s => absentStudentIds.has(s.id));
    let rollList = "";
    if (absentees.length > 0) {
        rollList = absentees.map((s, i) => `${i + 1}. ${s.roll_number} - ${s.name} (Parent: ${s.father_phone})`).join("\n");
    } else {
        rollList = "None (100% Attendance recorded)";
    }

    return `📊 *SSITS - DAILY ATTENDANCE SUMMARY REPORT* 📊
---------------------------------------------
🏛️ *Institution:* Sri Sai Institute of Technology & Science
🎓 *Program:* ${window.PROGRAM_NAME}
📌 *Department:* ${window.DEPT_NAME} (${window.DEPT_CODE})
📅 *Class:* ${window.YEAR_NAME}
📆 *Date:* ${dateVal} | *Session:* ${sessionLabel}
👨‍🏫 *Class Teacher:* ${window.TEACHER_NAME}
---------------------------------------------
📈 *Total Strength:* ${total}
✅ *Present Count:* ${present}
❌ *Absent Count:* ${absentCount}
📊 *Attendance Rate:* ${pct}%
---------------------------------------------
📋 *ABSENT STUDENTS LIST:*
${rollList}
---------------------------------------------
*Note: Absence alert notifications have been prepared for parents via WhatsApp.*`.trim();
}

// Open HOD Modal
function openHodSummaryModal() {
    const summaryMsg = generateHodSummaryMessage();
    document.getElementById("hodMessagePreview").value = summaryMsg;

    const encoded = encodeURIComponent(summaryMsg);
    const hodLink = `https://wa.me/91${window.HOD_PHONE}?text=${encoded}`;
    document.getElementById("btnSendToHodWhatsApp").setAttribute("href", hodLink);

    const modal = new bootstrap.Modal(document.getElementById("hodSummaryModal"));
    modal.show();
}

// Trigger PDF Report Download with Day Type & Occasion Name
function generatePdfReport() {
    const dateVal = document.getElementById("attendanceDate").value;
    const absentIds = Array.from(absentStudentIds).join(",");
    const downloadUrl = `/api/generate-pdf?date=${dateVal}&session=${currentSession}&absent_ids=${absentIds}&day_type=${currentDayType}&occasion_name=${encodeURIComponent(currentOccasionName)}`;
    
    window.open(downloadUrl, "_blank");
}

// -------------------------------------------------------------
// FACULTY MONTHLY ATTENDANCE SHEET & PARENT INQUIRY HELPERS
// -------------------------------------------------------------
let facultyMonthlyData = null;

function openFacultyMonthlyModal() {
    const modal = new bootstrap.Modal(document.getElementById("facultyMonthlyModal"));
    modal.show();
    loadFacultyMonthlyReport();
}

async function loadFacultyMonthlyReport() {
    const monthVal = document.getElementById("facultyMonthPicker").value;
    if (!monthVal) {
        alert("Please pick a month!");
        return;
    }
    const [y, m] = monthVal.split("-");
    const tbody = document.getElementById("facultyMonthlyTbody");
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Calculating class monthly attendance...</td></tr>`;

    try {
        const url = `/api/monthly-report?program_id=${window.PROGRAM_ID}&department_id=${window.DEPT_ID}&year_id=${window.YEAR_ID}&section=${window.SECTION}&year=${y}&month=${parseInt(m)}`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.status === "success") {
            facultyMonthlyData = data;
            const calDays = new Date(data.year, data.month, 0).getDate();
            document.getElementById("facMrepCalDays").innerText = calDays;
            document.getElementById("facMrepWorkDays").innerText = data.total_working_days;
            document.getElementById("facMrepHols").innerText = Math.max(0, calDays - data.total_working_days);

            let eligible = 0, condonation = 0, detained = 0;
            let html = "";
            (data.report_data || []).forEach((r, idx) => {
                if (r.percentage >= 75) eligible++;
                else if (r.percentage >= 65) condonation++;
                else detained++;

                const pctColor = r.percentage >= 75 ? "success" : (r.percentage >= 65 ? "warning" : "danger");
                html += `
                    <tr>
                        <td>${idx + 1}</td>
                        <td><strong class="text-primary">${r.roll_number}</strong></td>
                        <td class="fw-semibold text-dark">${r.name}</td>
                        <td class="text-muted">${r.father_name}</td>
                        <td class="text-center fw-bold">${r.total_working_days}</td>
                        <td class="text-center fw-bold text-success">${r.attended_days}</td>
                        <td class="text-center fw-bold text-danger">${r.absent_days}</td>
                        <td class="text-center fw-bold text-${pctColor}">${r.percentage}%</td>
                        <td class="text-center"><span class="badge ${r.eligibility_class} px-2 py-1">${r.eligibility}</span></td>
                    </tr>
                `;
            });

            document.getElementById("facMrepEligible").innerText = eligible;
            document.getElementById("facMrepCondonation").innerText = condonation;
            document.getElementById("facMrepDetained").innerText = detained;
            tbody.innerHTML = html || `<tr><td colspan="9" class="text-center py-4 text-muted">No students found.</td></tr>`;
        } else {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">${data.message}</td></tr>`;
        }
    } catch (err) {
        console.error(err);
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">Failed to load monthly sheet.</td></tr>`;
    }
}

function exportFacultyMonthlyCSV() {
    if (!facultyMonthlyData || !facultyMonthlyData.report_data) {
        alert("Please calculate monthly attendance first!");
        return;
    }
    const d = facultyMonthlyData;
    let csv = `Sri Sai Institute of Technology and Science (Autonomous)\n`;
    csv += `Class Monthly Attendance Report - ${d.month_name}\n`;
    csv += `Program: ${d.program_code}, Branch: ${d.department_code}, Year: ${d.year_name}, Section: ${d.section}\n`;
    csv += `Total Working Days: ${d.total_working_days}\n\n`;
    csv += `S.No,Roll Number,Student Name,Father Name,Parent Phone,Working Days,Attended Days,Absent Days,Attendance %,Status\n`;

    d.report_data.forEach((r, idx) => {
        csv += `${idx + 1},"${r.roll_number}","${r.name}","${r.father_name}","${r.father_phone}",${r.total_working_days},${r.attended_days},${r.absent_days},${r.percentage}%,"${r.eligibility}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Monthly_${d.dept_code}_Sec${d.section}_${d.month}_${d.year}.csv`;
    link.click();
}

function printFacultyMonthlyReport() {
    const monthVal = document.getElementById("facultyMonthPicker") ? document.getElementById("facultyMonthPicker").value : "";
    const originalTitle = document.title;
    document.title = `SSITS_Monthly_Attendance_${monthVal || "Report"}`;
    window.print();
    setTimeout(() => { document.title = originalTitle; }, 1000);
}

// Download Official Institutional Monthly Cumulative Attendance Report PDF
function downloadCumulativeMonthlyPdf() {
    const monthVal = document.getElementById("facultyMonthPicker") ? document.getElementById("facultyMonthPicker").value : "";
    if (!monthVal) {
        alert("Please pick an academic month first!");
        return;
    }
    const [y, m] = monthVal.split("-");
    const url = `/api/cumulative-monthly-pdf?program_id=${window.PROGRAM_ID}&department_id=${window.DEPT_ID}&year_id=${window.YEAR_ID}&section=${window.SECTION}&year=${y}&month=${parseInt(m)}`;
    window.open(url, "_blank");
}

function downloadStudentDossierPdf() {
    const sid = document.getElementById("facStudentSelect").value;
    if (!sid) {
        alert("Please choose a student from the list first!");
        return;
    }
    window.open(`/api/student-dossier-pdf?student_id=${sid}`, "_blank");
}

function populateFacStudentDropdown(list) {
    const select = document.getElementById("facStudentSelect");
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = '<option value="">-- Choose Student --</option>';
    (list || []).forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.innerText = `${s.roll_number} - ${s.name}`;
        select.appendChild(opt);
    });
    if (currentVal && Array.from(select.options).some(o => o.value == currentVal)) {
        select.value = currentVal;
    }
}

function onFacStudentSearchInput(query) {
    query = (query || "").trim().toLowerCase();
    if (!query) {
        populateFacStudentDropdown(students);
        return;
    }
    const filtered = (students || []).filter(s => 
        (s.roll_number && s.roll_number.toLowerCase().includes(query)) ||
        (s.name && s.name.toLowerCase().includes(query)) ||
        (s.father_name && s.father_name.toLowerCase().includes(query)) ||
        (s.father_phone && s.father_phone.includes(query))
    );
    populateFacStudentDropdown(filtered);

    // If exact or single match found, automatically load attendance history
    if (filtered.length === 1) {
        const select = document.getElementById("facStudentSelect");
        select.value = filtered[0].id;
        loadFacultyStudentDailyHistory();
    }
}

function openFacultyParentInquiryModal() {
    const searchInput = document.getElementById("facStudentSearchInput");
    if (searchInput) searchInput.value = "";
    populateFacStudentDropdown(students);

    document.getElementById("facDossierWrap").style.display = "none";
    const modalEl = document.getElementById("facultyParentInquiryModal");
    if (modalEl && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

async function loadFacultyStudentDailyHistory() {
    const sid = document.getElementById("facStudentSelect").value;
    if (!sid) {
        alert("Please choose a student first!");
        return;
    }
    const wrap = document.getElementById("facDossierWrap");
    const tbody = document.getElementById("facDailyLogsTbody");
    wrap.style.display = "block";
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-success me-2"></div>Loading attendance logs...</td></tr>`;

    try {
        const res = await fetch(`/api/student-daily-attendance?student_id=${sid}`);
        const data = await res.json();

        if (data.status === "success") {
            const s = data.student;
            document.getElementById("facDossierName").innerText = s.name;
            document.getElementById("facDossierRoll").innerText = s.roll_number;
            document.getElementById("facDossierFather").innerText = s.father_name || "-";
            document.getElementById("facDossierPhone").innerText = s.father_phone || "-";

            document.getElementById("facDossierTotal").innerText = data.total_tracked_days;
            document.getElementById("facDossierPresent").innerText = data.total_attended_days;
            document.getElementById("facDossierAbsent").innerText = data.total_absent_days;
            document.getElementById("facDossierPct").innerText = `${data.attendance_percentage}%`;

            const waMsg = encodeURIComponent(
                `🏫 SRI SAI INSTITUTE OF TECHNOLOGY AND SCIENCE (AUTONOMOUS)\n` +
                `📊 OFFICIAL STUDENT ATTENDANCE DOSSIER\n\n` +
                `Student: ${s.name} (${s.roll_number})\n` +
                `Class: ${s.dept_code} - ${s.year_name} (Section ${s.section})\n` +
                `Parent: ${s.father_name}\n\n` +
                `Total Sessions Tracked: ${data.total_tracked_days}\n` +
                `Sessions Present: ${data.total_attended_days}\n` +
                `Sessions Absent: ${data.total_absent_days}\n` +
                `Overall Attendance: ${data.attendance_percentage}%\n\n` +
                `Class Teacher: ${window.TEACHER_NAME} (${window.TEACHER_PHONE})`
            );
            document.getElementById("facDossierWaBtn").href = `https://wa.me/91${s.father_phone}?text=${waMsg}`;

            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No attendance logs found.</td></tr>`;
            } else {
                let html = "";
                data.history.forEach((h, idx) => {
                    let mBadge = h.morning_status === "present" ? '<span class="badge badge-present-pill">PRESENT</span>' : (h.morning_status === "absent" ? '<span class="badge badge-absent-pill">ABSENT</span>' : '<span class="badge bg-secondary">Not Marked</span>');
                    let aBadge = h.afternoon_status === "present" ? '<span class="badge badge-present-pill">PRESENT</span>' : (h.afternoon_status === "absent" ? '<span class="badge badge-absent-pill">ABSENT</span>' : '<span class="badge bg-secondary">Not Marked</span>');

                    html += `
                        <tr>
                            <td>${idx + 1}</td>
                            <td><strong class="text-navy">${h.date}</strong></td>
                            <td class="text-muted">${h.weekday}</td>
                            <td class="text-center">${mBadge}</td>
                            <td class="text-center">${aBadge}</td>
                            <td class="text-center"><span class="${h.badge_class} px-2 py-1">${h.overall_status}</span></td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            }
        } else {
            alert(data.message || "Failed to load student history.");
        }
    } catch (err) {
        console.error(err);
        alert("Network error fetching student history.");
    }
}
