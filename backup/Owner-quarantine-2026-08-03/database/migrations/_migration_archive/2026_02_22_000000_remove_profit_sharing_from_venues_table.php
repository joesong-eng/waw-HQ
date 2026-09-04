<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     * 
     * Remove profit sharing fields from venues table.
     * Profit sharing is handled at the Device level (share_device_owner, share_venue_owner),
     * not at the Venue level. Venues are just physical locations.
     */
    public function up(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->dropColumn(['share_owner', 'share_staff']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->decimal('share_owner', 5, 2)->default(60.00)->after('status');
            $table->decimal('share_staff', 5, 2)->default(40.00)->after('share_owner');
        });
    }
};
