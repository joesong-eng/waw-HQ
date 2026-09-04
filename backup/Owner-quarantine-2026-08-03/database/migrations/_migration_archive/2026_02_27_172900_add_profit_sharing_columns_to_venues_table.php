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
        Schema::table('venues', function (Blueprint $table) {
            // Add profit sharing columns
            $table->decimal('default_share_device_owner', 5, 2)->default(60.00)->after('status')
                ->comment('設備商預設分成百分比 (e.g. 60.00 = 60%)');
            $table->decimal('default_share_venue_owner', 5, 2)->default(40.00)->after('default_share_device_owner')
                ->comment('場地商預設分成百分比 (e.g. 40.00 = 40%)');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->dropColumn(['default_share_device_owner', 'default_share_venue_owner']);
        });
    }
};
