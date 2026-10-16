<?php
/**
 * Event Ticketing and Venue Booking System
 * Course: SWC3633 / SWC4443 Web API Development
 * Universiti Poly-Tech Malaysia (UPTM)
 * Theme: Chocolate, Cream, White & Black
 * XAMPP Integration & Server Launch Control Center
 */

$backend_host = "127.0.0.1";
$backend_port = 8000;
$backend_url = "http://{$backend_host}:{$backend_port}";

// Check if Python FastAPI server is currently running
$fp = @fsockopen($backend_host, $backend_port, $errno, $errstr, 1);
$is_server_running = ($fp !== false);
if ($is_server_running) {
    fclose($fp);
}

// Check MySQL Database Connection
$mysql_host = "127.0.0.1";
$mysql_user = "root";
$mysql_pass = "";
$mysql_db   = "event_ticketing_db";
$mysql_conn = @new mysqli($mysql_host, $mysql_user, $mysql_pass, $mysql_db);
$is_mysql_running = ($mysql_conn && !$mysql_conn->connect_error);

$stats = [
    'users' => 0,
    'venues' => 0,
    'events' => 0,
    'bookings' => 0
];
if ($is_mysql_running) {
    if ($res = $mysql_conn->query("SELECT COUNT(*) as c FROM users")) { $stats['users'] = $res->fetch_assoc()['c']; }
    if ($res = $mysql_conn->query("SELECT COUNT(*) as c FROM venues")) { $stats['venues'] = $res->fetch_assoc()['c']; }
    if ($res = $mysql_conn->query("SELECT COUNT(*) as c FROM events")) { $stats['events'] = $res->fetch_assoc()['c']; }
    if ($res = $mysql_conn->query("SELECT COUNT(*) as c FROM bookings")) { $stats['bookings'] = $res->fetch_assoc()['c']; }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TicketHub - XAMPP Control Hub &amp; REST API Portal</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --chocolate-dark: #2B1810;
      --chocolate-rich: #5C3826;
      --chocolate-hover: #43281A;
      --accent-gold: #C68B59;
      --accent-amber: #D4A373;
      --cream-canvas: #FAF7F2;
      --cream-surface: #F5EFEB;
      --cream-pill: #F3E9E0;
      --border-cream: #E8DFD5;
      --black-midnight: #140E0B;
      --text-black: #1F1814;
    }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--cream-canvas);
      color: var(--text-black);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .hero-banner {
      background: linear-gradient(135deg, #140E0B 0%, #2B1810 50%, #462818 100%);
      color: #FFFFFF;
      padding: 3rem 1rem 3.2rem;
      border-radius: 0 0 28px 28px;
      border-bottom: 2px solid #7B4B32;
      box-shadow: 0 12px 30px rgba(20, 14, 11, 0.35);
    }
    .status-badge {
      font-size: 0.85rem;
      padding: 0.45rem 1.1rem;
      border-radius: 50px;
      font-weight: 600;
    }
    .card-custom {
      border: 1px solid var(--border-cream);
      border-radius: 18px;
      background: #FFFFFF;
      transition: all 0.25s ease-in-out;
      box-shadow: 0 4px 14px rgba(43, 24, 16, 0.04);
    }
    .card-custom:hover {
      transform: translateY(-4px);
      box-shadow: 0 16px 32px -6px rgba(43, 24, 16, 0.16);
      border-color: var(--accent-gold);
    }
    .code-box {
      background: #140E0B;
      color: #F5EFEB;
      padding: 1.3rem;
      border-radius: 14px;
      font-family: 'Consolas', monospace;
      font-size: 0.9rem;
      line-height: 1.6;
      border: 1px solid #361E12;
    }
    .code-comment {
      color: var(--accent-amber);
    }
    .metric-badge {
      font-size: 1.6rem;
      font-weight: 800;
      color: var(--chocolate-rich);
    }
    .btn-chocolate {
      background-color: var(--chocolate-rich);
      border-color: var(--chocolate-rich);
      color: #FFFFFF;
      font-weight: 600;
      border-radius: 10px;
      transition: all 0.2s ease;
    }
    .btn-chocolate:hover {
      background-color: var(--chocolate-hover);
      border-color: var(--chocolate-hover);
      color: #FFFFFF;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(67, 40, 26, 0.3);
    }
    .btn-outline-chocolate {
      border-color: var(--chocolate-rich);
      color: var(--chocolate-rich);
      font-weight: 600;
      border-radius: 10px;
      transition: all 0.2s ease;
    }
    .btn-outline-chocolate:hover {
      background-color: var(--chocolate-rich);
      color: #FFFFFF;
      box-shadow: 0 4px 12px rgba(92, 56, 38, 0.25);
    }
    .brand-tag {
      background: linear-gradient(135deg, #7B4B32, #C68B59);
      color: #FFFFFF;
      padding: 4px 12px;
      border-radius: 50px;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
      font-weight: 700;
    }
  </style>
</head>
<body>

  <!-- Top Hero Header -->
  <div class="hero-banner text-center mb-4">
    <div class="container">
      <span class="brand-tag mb-3 d-inline-block">RESTFUL WEB API &bull; CONCERT &amp; VENUE PLATFORM</span>
      <h1 class="fw-bold mb-2">
        <i class="bi bi-ticket-perforated-fill text-gold me-2" style="color: #C68B59;"></i>Event Ticketing &amp; Venue Booking System
      </h1>
      <p class="mb-3 opacity-90" style="color: #F5EFEB;">
        Course: SWC3633 / SWC4443 Web API Development &bull; Universiti Poly-Tech Malaysia (UPTM)
      </p>

      <!-- Live Server & Database Status Indicators -->
      <div class="d-flex justify-content-center gap-2 flex-wrap">
        <?php if ($is_server_running): ?>
          <span class="status-badge bg-success text-white shadow-sm">
            <i class="bi bi-check-circle-fill me-1"></i> REST API Server ONLINE (:8000)
          </span>
        <?php else: ?>
          <span class="status-badge bg-warning text-dark shadow-sm">
            <i class="bi bi-exclamation-triangle-fill me-1"></i> REST API STOPPED (Start in PowerShell)
          </span>
        <?php endif; ?>

        <?php if ($is_mysql_running): ?>
          <span class="status-badge text-white shadow-sm" style="background-color: #5C3826; border: 1px solid #C68B59;">
            <i class="bi bi-database-fill-check me-1" style="color: #C68B59;"></i> MySQL event_ticketing_db CONNECTED (:3306)
          </span>
        <?php else: ?>
          <span class="status-badge bg-danger text-white shadow-sm">
            <i class="bi bi-database-fill-x me-1"></i> MySQL DISCONNECTED (Start MySQL in XAMPP)
          </span>
        <?php endif; ?>
      </div>
    </div>
  </div>

  <div class="container mb-5 flex-grow-1">

    <!-- Live Database Metrics -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        <div class="card card-custom p-3 text-center">
          <span class="text-muted small fw-medium">Registered Users</span>
          <div class="metric-badge"><?= $stats['users'] ?></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card card-custom p-3 text-center">
          <span class="text-muted small fw-medium">Approved Venues</span>
          <div class="metric-badge"><?= $stats['venues'] ?></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card card-custom p-3 text-center">
          <span class="text-muted small fw-medium">Live Events &amp; Concerts</span>
          <div class="metric-badge"><?= $stats['events'] ?></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card card-custom p-3 text-center">
          <span class="text-muted small fw-medium">Total Bookings</span>
          <div class="metric-badge"><?= $stats['bookings'] ?></div>
        </div>
      </div>
    </div>

    <!-- Action Cards -->
    <div class="row g-4 justify-content-center">

      <!-- Action Card 1: Launch Web Application -->
      <div class="col-md-4">
        <div class="card card-custom h-100 p-4 text-center">
          <div class="mb-3 display-5" style="color: #5C3826;"><i class="bi bi-browser-chrome"></i></div>
          <h4 class="fw-bold mb-2" style="color: #2B1810;">Full Web Application</h4>
          <p class="text-muted small mb-4">Browse Malaysian mega concerts &amp; events, book tickets, view live QR admission passes, and access Organiser/Admin tools.</p>
          <a href="<?= $is_server_running ? $backend_url : 'frontend/index.html' ?>" target="_blank" class="btn btn-chocolate py-2 mt-auto">
            <i class="bi bi-box-arrow-up-right me-1"></i> Open Web Portal
          </a>
        </div>
      </div>

      <!-- Action Card 2: Interactive Swagger UI Docs -->
      <div class="col-md-4">
        <div class="card card-custom h-100 p-4 text-center">
          <div class="mb-3 display-5" style="color: #C68B59;"><i class="bi bi-file-code-fill"></i></div>
          <h4 class="fw-bold mb-2" style="color: #2B1810;">OpenAPI / Swagger UI</h4>
          <p class="text-muted small mb-4">Interactively test all REST resource endpoints (<code>/users</code>, <code>/events</code>, <code>/venues</code>, <code>/bookings</code>, QR &amp; PDF).</p>
          <a href="<?= $backend_url ?>/docs" target="_blank" class="btn btn-outline-chocolate py-2 mt-auto <?= !$is_server_running ? 'disabled' : '' ?>">
            <i class="bi bi-braces me-1"></i> Open Swagger Docs
          </a>
        </div>
      </div>

      <!-- Action Card 3: ReDoc Documentation -->
      <div class="col-md-4">
        <div class="card card-custom h-100 p-4 text-center">
          <div class="mb-3 display-5" style="color: #2B1810;"><i class="bi bi-book-half"></i></div>
          <h4 class="fw-bold mb-2" style="color: #2B1810;">ReDoc Reference</h4>
          <p class="text-muted small mb-4">Clean publication-style REST API specifications and data schema definitions for academic assessment.</p>
          <a href="<?= $backend_url ?>/redoc" target="_blank" class="btn btn-outline-chocolate py-2 mt-auto <?= !$is_server_running ? 'disabled' : '' ?>">
            <i class="bi bi-journal-text me-1"></i> Open ReDoc
          </a>
        </div>
      </div>

    </div>

    <!-- How to Start in PowerShell Guide -->
    <div class="card card-custom mt-4 p-4">
      <h5 class="fw-bold mb-2" style="color: #2B1810;"><i class="bi bi-terminal me-2" style="color: #5C3826;"></i>How to Open &amp; Run the Server in PowerShell</h5>
      <p class="text-muted small mb-3">To launch the RESTful API server from PowerShell in this XAMPP directory:</p>

      <div class="code-box mb-3">
<span class="code-comment"># Step 1: Open PowerShell and navigate to the project directory:</span><br/>
cd "C:\xampp\htdocs\Event _ticketing_system"<br/><br/>
<span class="code-comment"># Step 2: Run the automated startup script:</span><br/>
.\start_server.ps1<br/><br/>
<span class="code-comment"># Or run directly with Python Uvicorn:</span><br/>
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
      </div>

      <div class="d-flex gap-2">
        <a href="start_server.bat" download class="btn btn-outline-chocolate btn-sm">
          <i class="bi bi-play-circle me-1"></i> Or double-click <code>start_server.bat</code>
        </a>
      </div>
    </div>

    <!-- Security & Role-Based Access Control Overview -->
    <div class="card card-custom mt-4 p-4">
      <h5 class="fw-bold mb-3" style="color: #2B1810;"><i class="bi bi-shield-check text-success me-2"></i>Security &amp; Role-Based Access Control (RBAC)</h5>
      <div class="row g-3">
        <div class="col-md-4">
          <div class="p-3 rounded border h-100" style="background-color: #FDFBF9; border-color: #E8DFD5 !important;">
            <h6 class="fw-bold mb-2" style="color: #B71C1C;"><i class="bi bi-shield-lock me-1"></i>Administrator Role</h6>
            <p class="small text-muted mb-0">Full control over users, venue approvals, system statistics, and external API audit monitoring.</p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 rounded border h-100" style="background-color: #FDFBF9; border-color: #E8DFD5 !important;">
            <h6 class="fw-bold mb-2" style="color: #7B4B32;"><i class="bi bi-megaphone me-1"></i>Organiser Role</h6>
            <p class="small text-muted mb-0">Publishes concerts &amp; events, allocates seating inventory, and validates attendee QR passes at venue entrance gates.</p>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 rounded border h-100" style="background-color: #FDFBF9; border-color: #E8DFD5 !important;">
            <h6 class="fw-bold mb-2" style="color: #5C3826;"><i class="bi bi-person me-1"></i>Customer Role</h6>
            <p class="small text-muted mb-0">Browses Malaysian concerts, reserves tickets with automated inventory decrement, and downloads official PDF passes.</p>
          </div>
        </div>
      </div>
      <div class="mt-3 p-3 rounded border small text-muted" style="background-color: #F5EFEB; border-color: #E8DFD5 !important;">
        <i class="bi bi-info-circle me-1" style="color: #5C3826;"></i> <strong>Security Standard:</strong> Credentials secured with <strong>Bcrypt (cost 10)</strong> password hashing. Sessions authenticated via stateless <strong>JWT (HS256)</strong> tokens or <strong>API Keys (`X-API-Key`)</strong>.
      </div>
    </div>

  </div>

  <footer class="text-center small py-4" style="background-color: #140E0B; color: #D7CCC8; border-top: 2px solid #2B1810;">
    Event Ticketing &amp; Venue Booking System &bull; Production-Grade RESTful API Architecture
  </footer>

</body>
</html>
