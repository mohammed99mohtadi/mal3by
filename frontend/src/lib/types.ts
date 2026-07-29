export type Court = { id:number; sport_id:number; name_en:string; name_ar:string; description_en?:string|null; description_ar?:string|null; area:string; address:string; price_per_hour:string; currency:string; capacity:number; image_url?:string|null; is_active:boolean; sport?:{name_en:string;name_ar:string;slug:string}|null };
export type Review = { id:number; rating:number; comment?:string|null; is_verified_booking:boolean; created_at:string; reviewer:{id:number;full_name:string}; owner_response?:{response_text:string}|null };
export type RatingSummary = { average_rating:string; total_reviews:number; verified_reviews:number; rating_distribution:{one:number;two:number;three:number;four:number;five:number} };
export type User = { id:number; full_name:string; email:string; phone_number?:string|null; role:string; is_active:boolean };
export type BookingStatus="pending"|"pending_payment"|"confirmed"|"cancelled"|"expired"|"completed"|"rejected"|"refunded";
export type Booking={id:number;court_id:number;start_time:string;end_time:string;total_price:string;currency:string;status:BookingStatus;hold_expires_at?:string|null;cancellation_reason?:string|null;cancelled_at?:string|null;created_at:string;court?:Court|null};
export class ApiError extends Error { constructor(public status:number, message:string){super(message)} }
