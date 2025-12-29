# REQUIRED ENVIRONMENT VARIABLES FOR RAILWAY DEPLOYMENT

## 🔴 CRITICAL - MUST PROVIDE

### **1. Supabase Credentials (for backup sync)**
```bash
SUPABASE_URL=https://uxnbnxvvijockfkzsyck.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here
```

### **2. AI Provider (at least one required)**
```bash
# Option A: OpenAI (recommended for production)
OPENAI_API_KEY=your_openai_api_key_here

# Option B: Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Option C: Ollama (self-hosted)
OLLAMA_URL=http://your-ollama-server:11434
```

### **3. Security**
```bash
SECRET_KEY=your_secure_random_secret_key_minimum_32_characters
```

## 🟡 AUTO-PROVIDED BY RAILWAY

### **These are automatically set when you deploy:**
```bash
DATABASE_URL=postgresql://...  # Auto-created when you add PostgreSQL service
PORT=8000                      # Auto-set by Railway
RAILWAY_ENVIRONMENT=production # Auto-set by Railway
```

## 🟢 OPTIONAL - SYSTEM WILL USE DEFAULTS

### **Database Configuration (optional)**
```bash
PRIMARY_DB=railway                    # Default: 'supabase', set to 'railway' for production
BACKUP_SYNC_ENABLED=true             # Default: 'true'
DUAL_WRITE=false                     # Default: 'false'
```

### **AI Configuration (optional)**
```bash
OLLAMA_MODEL=qwen2.5:7b              # Default model
AI_TIMEOUT=900                       # 15 minutes timeout
ENABLE_AGENTIC_ANALYSIS=true         # Enable advanced AI features
```

### **Performance Tuning (optional)**
```bash
DB_POOL_SIZE=25                      # Connection pool size (default: 25)
BACKUP_SYNC_INTERVAL=3600            # Sync every hour (default)
```

## 📝 DEPLOYMENT CHECKLIST

### ✅ **Pre-Deployment**
- [ ] Get Supabase credentials from your dashboard
- [ ] Get AI provider API key (OpenAI/Anthropic/Ollama URL)
- [ ] Generate secure SECRET_KEY (min 32 characters)

### ✅ **Railway Deployment**
- [ ] Run `railway up` to deploy
- [ ] Run `railway add postgresql` to add database
- [ ] Set environment variables with `railway variables set`
- [ ] Run schema setup: `railway run python migration_scripts/setup_railway_schema.py`

### ✅ **Post-Deployment Verification**
- [ ] Check `/health` endpoint works
- [ ] Check `/api/database/health` shows Railway as primary
- [ ] Test resume upload and analysis
- [ ] Verify backup sync is working

## 🚨 WHAT YOU NEED TO PROVIDE RIGHT NOW

**Just send me these 3 things:**

1. **Supabase Anon Key**: `eyJ...` (from your Supabase dashboard)
2. **Supabase Service Role Key**: `eyJ...` (from your Supabase dashboard)  
3. **AI Provider API Key**: Either OpenAI or Anthropic API key

That's it! Everything else is either auto-generated or has sensible defaults.
