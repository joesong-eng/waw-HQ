<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('daily_revenue_reports', function (Blueprint $table) {
            $table->unsignedBigInteger('device_id')->after('venue_id')->nullable();
            
            // Drop old unique constraint if it exists (venue_id, report_date)
            // Note: Different DB systems handle this differently, but for MySQL/SQLite:
            // $table->dropUnique(['venue_id', 'report_date']);
            
            $table->foreign('device_id')->references('id')->on('devices')->onDelete('cascade');
            $table->index(['device_id', 'report_date']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('daily_revenue_reports', function (Blueprint $table) {
            $table->dropForeign(['device_id']);
            $table->dropColumn('device_id');
        });
    }
};
