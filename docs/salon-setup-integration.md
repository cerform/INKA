# Salon Setup Landing Page - Integration Guide

## Overview

A comprehensive multi-language setup wizard for new salon administrators to configure their salon on the INKA platform.

## Features

✅ **Multi-Step Wizard**
- Step 1: Basic Information (Salon name, Timezone)
- Step 2: Specializations (Tattoo, Piercing, Nail Art, Beauty, Multiple)
- Step 3: Work Schedule (Configure daily hours, days off)
- Step 4: Integration Keys (Telegram Bot Token - optional)
- Step 5: Success with API Key generation

✅ **Multilingual Support**
- English (en)
- Russian (ru) 
- Hebrew (he)
- Auto-detection from browser/localStorage
- Language switcher in UI

✅ **Modern UI**
- Progress indicator
- Form validation
- Error handling
- Loading states
- Responsive design (mobile/tablet/desktop)

## Backend API Endpoints

All endpoints require authentication header: `Authorization: Bearer {token}`

### 1. Initialize Salon Setup
**POST** `/api/v1/setup/salon-init`

Request Body:
```json
{
  "salon_name": "My Tattoo Shop",
  "specialization": "tattoo",
  "timezone": "Europe/Paris",
  "telegram_bot_token": "123456789:ABCdeF...",
  "work_schedule": [
    {
      "day_of_week": "monday",
      "is_working": true,
      "start_time": "09:00",
      "end_time": "21:00"
    },
    {
      "day_of_week": "sunday",
      "is_working": false,
      "start_time": "00:00",
      "end_time": "00:00"
    }
  ]
}
```

Response:
```json
{
  "status": "success",
  "message": "Salon setup initialized",
  "data": {
    "salon_id": "123e4567-e89b-12d3-a456-426614174000",
    "api_key": "sk_abc123def456...",
    "salon_name": "My Tattoo Shop",
    "is_completed": false
  }
}
```

### 2. Get Setup Status
**GET** `/api/v1/setup/salon-status`

Response:
```json
{
  "status": "in_progress",
  "message": "Salon setup in progress",
  "data": {
    "salon_id": "123e4567-e89b-12d3-a456-426614174000",
    "is_completed": false,
    "completion_percentage": 40
  }
}
```

### 3. Update Setup Fields
**PUT** `/api/v1/setup/salon-update`

Request Body:
```json
{
  "salon_name": "Updated Name",
  "timezone": "Europe/London"
}
```

### 4. Retrieve API Key
**GET** `/api/v1/setup/api-key`

Response:
```json
{
  "status": "success",
  "data": {
    "api_key": "sk_abc123def456..."
  }
}
```

## Database Models

### SalonSetup
Stores salon configuration for a specific salon/admin.

Fields:
- `id` (UUID): Primary key
- `admin_id` (UUID): Link to admin user
- `salon_name` (str): Name of the salon
- `specialization` (str): Main service offered
- `timezone` (str): Admin's timezone
- `telegram_bot_token` (str, optional): Telegram bot API token
- `api_key` (str): Generated secret key for API access
- `is_completed` (bool): Setup completion status
- `is_active` (bool): Account active status
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### SalonWorkSchedule
Stores weekly work schedule configuration.

Fields:
- `id` (UUID): Primary key
- `salon_setup_id` (UUID): Reference to SalonSetup
- `day_of_week` (str): Day name (monday-sunday)
- `is_working` (bool): Whether salon is open
- `start_time` (time): Opening time (HH:MM format)
- `end_time` (time): Closing time (HH:MM format)

## Frontend Components

### File Structure
```
apps/admin/src/
├── pages/
│   ├── SalonSetup.tsx          # Main wizard component
│   └── SalonSetup.css          # Styling
├── locales/
│   └── setup.json              # i18n translations (en, ru, he)
├── i18n/
│   └── config.ts               # i18next configuration
└── App.tsx                      # Router setup
```

### Component Usage

Located at: `/src/pages/SalonSetup.tsx`

```tsx
import SalonSetup from '@/pages/SalonSetup';

// Route setup already configured in App.tsx:
// <Route path="/setup/salon" element={<SalonSetup />} />
```

### Key Features

1. **Language Switching**
   - Manual buttons in top-right corner
   - Auto-detection from browser/localStorage
   - Persistent storage in localStorage

2. **Form State Management**
   ```tsx
   interface FormData {
     salon_name: string;
     specialization: string;
     timezone: string;
     telegram_bot_token: string;
     work_schedule: WorkSchedule[];
   }
   ```

3. **Validation**
   - Salon name required
   - Bot token length check (if provided)
   - Time validation (end_time > start_time)

4. **API Integration**
   - Calls `/api/v1/setup/salon-init` on submission
   - Expects auth token in localStorage
   - Handles loading and error states
   - Displays API key in success screen with copy functionality

## Translation Keys

All keys follow the pattern: `setup.{key}`

### Core Keys
- `setup.title` - Wizard title
- `setup.subtitle` - Wizard subtitle
- `setup.step1-4` - Step titles
- `setup.next`, `setup.prev`, `setup.finish` - Buttons
- `setup.success` - Success message

### Form Labels
- `setup.salonName` - Salon name label
- `setup.salonNamePlaceholder` - Placeholder text
- `setup.specialization` - Specialization label
- `setup.timezone` - Timezone label
- `setup.telegramBotToken` - Bot token label
- `setup.botTokenPlaceholder` - Bot token placeholder

### Service Types
- `setup.tattoo` - Tattoo
- `setup.piercing` - Piercing
- `setup.nailArt` - Nail Art
- `setup.beauty` - Beauty Services
- `setup.multiple` - Multiple Services

### Days
- `setup.monday` through `setup.sunday`

## Usage Flow

### For New Salon Admins

1. **Access**: Navigate to `/setup/salon` after logging in
2. **Step 1**: Enter salon name and select timezone
3. **Step 2**: Select primary specialization
4. **Step 3**: Configure work schedule (select working days and hours)
5. **Step 4**: Optionally add Telegram bot token
6. **Step 5**: Submit and receive API key
7. **Success**: Copy API key and proceed to dashboard

### For Integration

```bash
# Access points:
- Development: http://localhost:5173/setup/salon
- Production: https://inka-admin-408800151466.europe-west1.run.app/setup/salon
```

### Environment Requirements

Frontend:
- React 18+
- React Router DOM
- react-i18next
- TypeScript

Backend:
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- Database with UUID support

## Styling

### CSS Features
- Gradient backgrounds
- Smooth animations
- Responsive design
- Mobile-first approach
- Accessibility-friendly colors

### Custom Theme
Colors used:
- Primary: #667eea (purple-blue)
- Secondary: #764ba2 (purple)
- Success: #51cf66 (green)
- Error: #c33 (red)
- Neutral: #333 (dark), #999 (gray), #ddd (light gray)

## Known Limitations

1. Bot token validation is length-based (minimum 20 chars) - actual validation happens server-side
2. API key is generated but not validated at frontend
3. No duplicate salon name checking
4. Work schedule doesn't support breaks within a day
5. Timezone list is predefined (can be expanded)

## Future Enhancements

- [ ] Break times configuration
- [ ] Multiple specializations selection
- [ ] Services and pricing configuration
- [ ] Staff member setup
- [ ] Calendar sync options
- [ ] Taxes and fees configuration
- [ ] Payment method integration

## Testing

### Manual Testing Checklist
- [ ] Wizard progresses through all 5 steps
- [ ] Language switching works (all 3 languages)
- [ ] Form validation prevents next button when invalid
- [ ] API key displays correctly on success
- [ ] Copy to clipboard works
- [ ] Responsive on mobile/tablet/desktop
- [ ] Error handling works for API failures
- [ ] Loading state shows during submission

### Test Credentials
Use a valid auth token from your authentication system:
```
localStorage.setItem('token', 'your_jwt_token_here');
```

## Troubleshooting

### Issue: Translations not showing

**Solution**: Ensure i18n config is loaded before component renders
```tsx
// In App.tsx or main entry point
import './i18n/config';
```

### Issue: API calls fail with 401

**Solution**: Check that auth token is present in localStorage
```tsx
const token = localStorage.getItem('token');
console.log('Token present:', !!token);
```

### Issue: Form won't submit

**Solution**: Check browser console for validation errors and ensure:
1. Salon name is not empty
2. At least one work day is configured
3. Auth token is valid

## Related Files

- Backend models: `/apps/api/src/app/domains/setup/models.py`
- Backend schemas: `/apps/api/src/app/domains/setup/schemas.py`
- Backend API: `/apps/api/src/app/domains/setup/api.py`
- Frontend component: `/apps/admin/src/pages/SalonSetup.tsx`
- Frontend styling: `/apps/admin/src/pages/SalonSetup.css`
- Translations: `/apps/admin/src/locales/setup.json`
- i18n config: `/apps/admin/src/i18n/config.ts`
