<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            // Add new columns
            $table->unsignedBigInteger('owner_id')->after('id');
            $table->string('timezone', 50)->default('UTC')->after('name');
            $table->string('currency', 3)->default('USD')->after('timezone');
            $table->decimal('share_owner', 5, 2)->default(60.00)->after('status');
            $table->decimal('share_staff', 5, 2)->default(40.00)->after('share_owner');
            $table->unsignedBigInteger('contact_staff_id')->nullable()->after('share_staff');
            $table->decimal('geo_lat', 10, 8)->nullable()->after('address');
            $table->decimal('geo_lng', 11, 8)->nullable()->after('geo_lat');

            // Update status enum to include new values
            $table->dropColumn('status');
            $table->enum('status', ['active', 'suspended', 'closed'])->default('active')->after('currency');

            // Add foreign keys
            $table->foreign('owner_id')->references('id')->on('users')->onDelete('cascade');
            $table->foreign('contact_staff_id')->references('id')->on('users')->onDelete('set null');

            // Add indexes
            $table->index('owner_id');
            $table->index('status');
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('venues', function (Blueprint $table) {
            $table->dropForeign(['owner_id']);
            $table->dropForeign(['contact_staff_id']);
            $table->dropIndex(['owner_id']);
            $table->dropIndex(['status']);
            $table->dropIndex(['created_at']);
            
            $table->dropColumn([
                'owner_id',
                'timezone',
                'currency',
                'share_owner',
                'share_staff',
                'contact_staff_id',
                'geo_lat',
                'geo_lng',
            ]);

            $table->enum('status', ['active', 'inactive'])->default('active')->change();
        });
    }
};
