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
        Schema::table('device_snapshots', function (Blueprint $table) {
            $table->timestamp('executed_at')->nullable()->after('snapshot_at')->comment('實際執行快照的時間');
            $table->index('executed_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('device_snapshots', function (Blueprint $table) {
            $table->dropIndex(['executed_at']);
            $table->dropColumn('executed_at');
        });
    }
};
