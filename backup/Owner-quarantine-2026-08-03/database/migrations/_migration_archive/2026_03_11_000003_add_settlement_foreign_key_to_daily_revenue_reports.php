<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * 
     * 添加 settlement_id 外鍵約束到 daily_revenue_reports 表
     * 注意：settlement_id 欄位已存在，只需添加外鍵約束
     */
    public function up(): void
    {
        Schema::table('daily_revenue_reports', function (Blueprint $table) {
            // 添加外鍵約束
            $table->foreign('settlement_id')
                  ->references('id')
                  ->on('settlements')
                  ->onDelete('set null');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('daily_revenue_reports', function (Blueprint $table) {
            // 移除外鍵約束
            $table->dropForeign(['settlement_id']);
        });
    }
};
